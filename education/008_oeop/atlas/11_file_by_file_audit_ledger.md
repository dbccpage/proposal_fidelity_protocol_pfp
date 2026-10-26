> **HISTORICAL.** This ledger is the coverage proof for frozen commit `c86134f8`, including `.agents/operad/**`. That directory is absent. The live path record is [chapter 23](23_plan_oewas_consolidation_oeeis_and_demo_integration.md).

# File-by-File Audit Ledger

This is the closed coverage proof for the audit base
`c86134f8c05c2b530607e3ec0c882c63d230d3f6`. It contains every tracked path under
`omega_engine_workflows_agents_skills/**` and `.agents/operad/**` exactly once.
The working-tree atlas itself is not part of the frozen input inventory and is
validated separately.

- Total paths: 231
- OEWAS paths: 166
- Reference-operad paths: 65
- Status for every row: reviewed
- Blob column: first 12 hexadecimal characters of the exact Git blob

“Reviewed” means the path was classified, read or structurally/visually inspected
as appropriate, and reconciled to the owning chapter. It is not an assertion that
the artifact is correct. Duplicated OEWAS image/model-guide pairs were additionally
verified byte-identical across `_img` and `_docs/_img`.

| # | Path | Blob | Kind | Owner |
| ---: | --- | --- | --- | ---: |
| 1 | `.agents/operad/OWNERSHIP.md` | `93fccd6397bf` | document | [08](08_reference_operad_and_skill_compiler.md) |
| 2 | `.agents/operad/SEMANTICS_MAP.md` | `20edb7a8de53` | document | [08](08_reference_operad_and_skill_compiler.md) |
| 3 | `.agents/operad/agent_capability_slices.json` | `43d1f60df748` | manifest/data | [08](08_reference_operad_and_skill_compiler.md) |
| 4 | `.agents/operad/antibodies.py` | `3c90299e7cf9` | source | [08](08_reference_operad_and_skill_compiler.md) |
| 5 | `.agents/operad/application/__init__.py` | `da3953074bd9` | package marker | [08](08_reference_operad_and_skill_compiler.md) |
| 6 | `.agents/operad/application/dto/operad_dto.py` | `4463b3deb297` | source | [08](08_reference_operad_and_skill_compiler.md) |
| 7 | `.agents/operad/application/use_cases/dispatch_operation_use_case.py` | `f2d0060d2d84` | source | [08](08_reference_operad_and_skill_compiler.md) |
| 8 | `.agents/operad/application/use_cases/record_trace_use_case.py` | `61641f6c9c39` | script/gate | [08](08_reference_operad_and_skill_compiler.md) |
| 9 | `.agents/operad/application/use_cases/validate_operad_use_case.py` | `75e2f004ed8c` | script/gate | [08](08_reference_operad_and_skill_compiler.md) |
| 10 | `.agents/operad/bulk_operad_ingest.py` | `b2979135b888` | script/gate | [08](08_reference_operad_and_skill_compiler.md) |
| 11 | `.agents/operad/colored_operad.py` | `e6a874d1d051` | source | [08](08_reference_operad_and_skill_compiler.md) |
| 12 | `.agents/operad/coloured_operad.py` | `aefd5e46e259` | source | [08](08_reference_operad_and_skill_compiler.md) |
| 13 | `.agents/operad/composition_matrix.json` | `595a67b31ba4` | manifest/data | [08](08_reference_operad_and_skill_compiler.md) |
| 14 | `.agents/operad/dispatch.py` | `fb4493a41ca1` | source | [08](08_reference_operad_and_skill_compiler.md) |
| 15 | `.agents/operad/domain/__init__.py` | `21ab9a939192` | package marker | [08](08_reference_operad_and_skill_compiler.md) |
| 16 | `.agents/operad/domain/antibodies.py` | `3bdac58447f2` | source | [08](08_reference_operad_and_skill_compiler.md) |
| 17 | `.agents/operad/domain/colours.py` | `1c5e6c418af3` | source | [08](08_reference_operad_and_skill_compiler.md) |
| 18 | `.agents/operad/domain/errors.py` | `bd9906609b45` | source | [08](08_reference_operad_and_skill_compiler.md) |
| 19 | `.agents/operad/domain/evidence.py` | `45bdb8ad3a7f` | source | [08](08_reference_operad_and_skill_compiler.md) |
| 20 | `.agents/operad/domain/hott.py` | `7fe406be9758` | source | [08](08_reference_operad_and_skill_compiler.md) |
| 21 | `.agents/operad/domain/operad.py` | `310ca0647af5` | source | [08](08_reference_operad_and_skill_compiler.md) |
| 22 | `.agents/operad/domain/operation.py` | `f20bd06d8fbf` | source | [08](08_reference_operad_and_skill_compiler.md) |
| 23 | `.agents/operad/domain/planar.py` | `2c7b84fcc902` | source | [08](08_reference_operad_and_skill_compiler.md) |
| 24 | `.agents/operad/domain/quotient.py` | `3b2f8d9f7d18` | source | [08](08_reference_operad_and_skill_compiler.md) |
| 25 | `.agents/operad/evidence_observations.py` | `b2347086f79f` | source | [08](08_reference_operad_and_skill_compiler.md) |
| 26 | `.agents/operad/evidence_receipt.py` | `7727def499d9` | source | [08](08_reference_operad_and_skill_compiler.md) |
| 27 | `.agents/operad/evidence_trace.json` | `1fec0895adf2` | manifest/data | [08](08_reference_operad_and_skill_compiler.md) |
| 28 | `.agents/operad/execute_operadic_compression.py` | `d2397dfa9f29` | script/gate | [08](08_reference_operad_and_skill_compiler.md) |
| 29 | `.agents/operad/hott.py` | `0d3d4d1203a3` | source | [08](08_reference_operad_and_skill_compiler.md) |
| 30 | `.agents/operad/hott_lite.py` | `d7b49d51f3ca` | source | [08](08_reference_operad_and_skill_compiler.md) |
| 31 | `.agents/operad/infrastructure/__init__.py` | `938c9dac59f3` | package marker | [08](08_reference_operad_and_skill_compiler.md) |
| 32 | `.agents/operad/infrastructure/adapters/file_lock_adapter.py` | `e35ab0884c7c` | source | [08](08_reference_operad_and_skill_compiler.md) |
| 33 | `.agents/operad/infrastructure/repositories/json_operad_repository.py` | `a85654cb72cb` | source | [08](08_reference_operad_and_skill_compiler.md) |
| 34 | `.agents/operad/operad_signature.json` | `0fbcf2bdc040` | manifest/data | [08](08_reference_operad_and_skill_compiler.md) |
| 35 | `.agents/operad/quotient_operad.py` | `9a63624386a9` | source | [08](08_reference_operad_and_skill_compiler.md) |
| 36 | `.agents/operad/record_trace.py` | `a07170006f5d` | script/gate | [08](08_reference_operad_and_skill_compiler.md) |
| 37 | `.agents/operad/residual_honesty.py` | `2059b1af3f06` | source | [08](08_reference_operad_and_skill_compiler.md) |
| 38 | `.agents/operad/scripts/compile_operad_signatures.py` | `cdb247e60ab7` | script/gate | [08](08_reference_operad_and_skill_compiler.md) |
| 39 | `.agents/operad/scripts/sync_agent_profiles.py` | `4fe98d98eaee` | script/gate | [08](08_reference_operad_and_skill_compiler.md) |
| 40 | `.agents/operad/skill_compiler/README.md` | `42fdae3cd590` | document | [08](08_reference_operad_and_skill_compiler.md) |
| 41 | `.agents/operad/skill_compiler/__init__.py` | `08a0cbcec9e4` | package marker | [08](08_reference_operad_and_skill_compiler.md) |
| 42 | `.agents/operad/skill_compiler/budget_exceptions.yaml` | `5b621690ed8c` | manifest/data | [08](08_reference_operad_and_skill_compiler.md) |
| 43 | `.agents/operad/skill_compiler/budget_gate.py` | `db57ef3708fb` | source | [08](08_reference_operad_and_skill_compiler.md) |
| 44 | `.agents/operad/skill_compiler/episode.py` | `83e01b17d572` | source | [08](08_reference_operad_and_skill_compiler.md) |
| 45 | `.agents/operad/skill_compiler/eval_runner.py` | `209f49fdc908` | source | [08](08_reference_operad_and_skill_compiler.md) |
| 46 | `.agents/operad/skill_compiler/knowledge_parity.py` | `be78fd419519` | source | [08](08_reference_operad_and_skill_compiler.md) |
| 47 | `.agents/operad/skill_compiler/metrics.py` | `dd92facf5321` | source | [08](08_reference_operad_and_skill_compiler.md) |
| 48 | `.agents/operad/skill_compiler/promote.py` | `06c31ab12fef` | source | [08](08_reference_operad_and_skill_compiler.md) |
| 49 | `.agents/operad/skill_compiler/resolve.py` | `032d77452c5a` | source | [08](08_reference_operad_and_skill_compiler.md) |
| 50 | `.agents/operad/skill_compiler/routes.yaml` | `f07d292e7223` | manifest/data | [08](08_reference_operad_and_skill_compiler.md) |
| 51 | `.agents/operad/skill_compiler/test_budget_gate.py` | `dc1e8fb2112d` | test | [09](09_testing_and_falsification.md) |
| 52 | `.agents/operad/skill_compiler/tests/test_episode_contract.py` | `7d68a8643965` | test | [09](09_testing_and_falsification.md) |
| 53 | `.agents/operad/skill_compiler/tests/test_eval_bank.py` | `9b20aa5468dc` | test | [09](09_testing_and_falsification.md) |
| 54 | `.agents/operad/skill_compiler/tests/test_skill_compiler.py` | `4a279b32fc15` | test | [09](09_testing_and_falsification.md) |
| 55 | `.agents/operad/symmetric_quotient.py` | `0b15c97fbcea` | source | [08](08_reference_operad_and_skill_compiler.md) |
| 56 | `.agents/operad/test_associativity_witness.py` | `1a549f9bb39a` | test | [09](09_testing_and_falsification.md) |
| 57 | `.agents/operad/test_coloured_operad_premiere.py` | `7d20b48c4042` | test | [09](09_testing_and_falsification.md) |
| 58 | `.agents/operad/test_dispatch_resolution.py` | `8324e0a485c1` | test | [09](09_testing_and_falsification.md) |
| 59 | `.agents/operad/test_domain_clean_arch.py` | `26d7bda8e386` | test | [09](09_testing_and_falsification.md) |
| 60 | `.agents/operad/test_evidence_observation_quarantine.py` | `fcf9f56ba2fe` | test | [09](09_testing_and_falsification.md) |
| 61 | `.agents/operad/test_operad_hardening.py` | `781944630bc4` | test | [09](09_testing_and_falsification.md) |
| 62 | `.agents/operad/test_phase3_honesty.py` | `de469fe86f10` | test | [09](09_testing_and_falsification.md) |
| 63 | `.agents/operad/test_skill_cull_references.py` | `11b501c38266` | test | [09](09_testing_and_falsification.md) |
| 64 | `.agents/operad/validate_operad.py` | `edfa32e9b811` | script/gate | [08](08_reference_operad_and_skill_compiler.md) |
| 65 | `.agents/operad/was_dto_schemas.py` | `d077f5bccdef` | source | [08](08_reference_operad_and_skill_compiler.md) |
| 66 | `omega_engine_workflows_agents_skills/__init__.py` | `f6250dd28a91` | package marker | [05](05_workflow_validation_and_interfaces.md) |
| 67 | `omega_engine_workflows_agents_skills/_docs/00_index.md` | `da285e06f6ed` | document | [12](12_open_issues_nonclaims_and_roadmap.md) |
| 68 | `omega_engine_workflows_agents_skills/_docs/01_spec_polarized_operad_and_anti_skills.md` | `76bc1656d648` | document | [12](12_open_issues_nonclaims_and_roadmap.md) |
| 69 | `omega_engine_workflows_agents_skills/_docs/02_review_applied_workflow_operad.md` | `c8602b8a3c59` | document | [12](12_open_issues_nonclaims_and_roadmap.md) |
| 70 | `omega_engine_workflows_agents_skills/_docs/03_lookup_archive_and_autop_inventory.md` | `138f03c9a2fb` | document | [12](12_open_issues_nonclaims_and_roadmap.md) |
| 71 | `omega_engine_workflows_agents_skills/_docs/04_guide_oewas_test_suite_execution.md` | `73ccb8408d42` | document | [12](12_open_issues_nonclaims_and_roadmap.md) |
| 72 | `omega_engine_workflows_agents_skills/_docs/05_notes_oewas_integration_plan_and_system_topology.md` | `999643ce9e44` | document | [12](12_open_issues_nonclaims_and_roadmap.md) |
| 73 | `omega_engine_workflows_agents_skills/_docs/06_spec_woland_7act_dialectic_workflow.md` | `2918b038a13c` | document | [12](12_open_issues_nonclaims_and_roadmap.md) |
| 74 | `omega_engine_workflows_agents_skills/_docs/07_spec_skill_consolidation_and_deep_modules.md` | `a685672681ae` | document | [12](12_open_issues_nonclaims_and_roadmap.md) |
| 75 | `omega_engine_workflows_agents_skills/_docs/08_spec_oewas_v3_production_engine.md` | `eeeb38b539ce` | document | [12](12_open_issues_nonclaims_and_roadmap.md) |
| 76 | `omega_engine_workflows_agents_skills/_docs/_img/00_clean_architecture_layers.png` | `620b1492cb88` | diagram | [12](12_open_issues_nonclaims_and_roadmap.md) |
| 77 | `omega_engine_workflows_agents_skills/_docs/_img/00_clean_architecture_layers.svg` | `b1ef23aa7c40` | diagram | [12](12_open_issues_nonclaims_and_roadmap.md) |
| 78 | `omega_engine_workflows_agents_skills/_docs/_img/01_operad_agent_skill_metaskill.png` | `2819690de6ad` | diagram | [12](12_open_issues_nonclaims_and_roadmap.md) |
| 79 | `omega_engine_workflows_agents_skills/_docs/_img/01_operad_agent_skill_metaskill.svg` | `a942ffbe3bf5` | diagram | [12](12_open_issues_nonclaims_and_roadmap.md) |
| 80 | `omega_engine_workflows_agents_skills/_docs/_img/02_operands_instructions_ast.png` | `3685a7e44ee8` | diagram | [12](12_open_issues_nonclaims_and_roadmap.md) |
| 81 | `omega_engine_workflows_agents_skills/_docs/_img/02_operands_instructions_ast.svg` | `c1dd406e0e9f` | diagram | [12](12_open_issues_nonclaims_and_roadmap.md) |
| 82 | `omega_engine_workflows_agents_skills/_docs/_img/03_residual_geometry_authority.png` | `819442917018` | diagram | [12](12_open_issues_nonclaims_and_roadmap.md) |
| 83 | `omega_engine_workflows_agents_skills/_docs/_img/03_residual_geometry_authority.svg` | `1d82d3005cba` | diagram | [12](12_open_issues_nonclaims_and_roadmap.md) |
| 84 | `omega_engine_workflows_agents_skills/_docs/_img/04_skills_vs_antiskills_obstruction.png` | `889154cc3a14` | diagram | [12](12_open_issues_nonclaims_and_roadmap.md) |
| 85 | `omega_engine_workflows_agents_skills/_docs/_img/04_skills_vs_antiskills_obstruction.svg` | `83710c39ae93` | diagram | [12](12_open_issues_nonclaims_and_roadmap.md) |
| 86 | `omega_engine_workflows_agents_skills/_docs/_img/oewas_operad_model_guide.md` | `6eb7fc11927e` | document | [12](12_open_issues_nonclaims_and_roadmap.md) |
| 87 | `omega_engine_workflows_agents_skills/_img/00_clean_architecture_layers.png` | `620b1492cb88` | diagram | [12](12_open_issues_nonclaims_and_roadmap.md) |
| 88 | `omega_engine_workflows_agents_skills/_img/00_clean_architecture_layers.svg` | `b1ef23aa7c40` | diagram | [12](12_open_issues_nonclaims_and_roadmap.md) |
| 89 | `omega_engine_workflows_agents_skills/_img/01_operad_agent_skill_metaskill.png` | `2819690de6ad` | diagram | [12](12_open_issues_nonclaims_and_roadmap.md) |
| 90 | `omega_engine_workflows_agents_skills/_img/01_operad_agent_skill_metaskill.svg` | `a942ffbe3bf5` | diagram | [12](12_open_issues_nonclaims_and_roadmap.md) |
| 91 | `omega_engine_workflows_agents_skills/_img/02_operands_instructions_ast.png` | `3685a7e44ee8` | diagram | [12](12_open_issues_nonclaims_and_roadmap.md) |
| 92 | `omega_engine_workflows_agents_skills/_img/02_operands_instructions_ast.svg` | `c1dd406e0e9f` | diagram | [12](12_open_issues_nonclaims_and_roadmap.md) |
| 93 | `omega_engine_workflows_agents_skills/_img/03_residual_geometry_authority.png` | `819442917018` | diagram | [12](12_open_issues_nonclaims_and_roadmap.md) |
| 94 | `omega_engine_workflows_agents_skills/_img/03_residual_geometry_authority.svg` | `1d82d3005cba` | diagram | [12](12_open_issues_nonclaims_and_roadmap.md) |
| 95 | `omega_engine_workflows_agents_skills/_img/04_skills_vs_antiskills_obstruction.png` | `889154cc3a14` | diagram | [12](12_open_issues_nonclaims_and_roadmap.md) |
| 96 | `omega_engine_workflows_agents_skills/_img/04_skills_vs_antiskills_obstruction.svg` | `83710c39ae93` | diagram | [12](12_open_issues_nonclaims_and_roadmap.md) |
| 97 | `omega_engine_workflows_agents_skills/_img/oewas_operad_model_guide.md` | `6eb7fc11927e` | document | [12](12_open_issues_nonclaims_and_roadmap.md) |
| 98 | `omega_engine_workflows_agents_skills/application/__init__.py` | `89ac4d7fe9aa` | package marker | [05](05_workflow_validation_and_interfaces.md) |
| 99 | `omega_engine_workflows_agents_skills/application/anti_skill_admission/__init__.py` | `3acd268fe71d` | package marker | [06](06_persistence_provenance_security_and_receipts.md) |
| 100 | `omega_engine_workflows_agents_skills/application/anti_skill_admission/generate_truth_boundary_canary.py` | `e35dcc0d64a3` | source | [06](06_persistence_provenance_security_and_receipts.md) |
| 101 | `omega_engine_workflows_agents_skills/application/anti_skill_admission/load_truth_boundary_activation.py` | `16a487a5c572` | source | [06](06_persistence_provenance_security_and_receipts.md) |
| 102 | `omega_engine_workflows_agents_skills/application/anti_skill_admission/verifier.py` | `248978cae95b` | source | [06](06_persistence_provenance_security_and_receipts.md) |
| 103 | `omega_engine_workflows_agents_skills/application/commands/__init__.py` | `6790afb41750` | package marker | [05](05_workflow_validation_and_interfaces.md) |
| 104 | `omega_engine_workflows_agents_skills/application/commands/compile_catalog.py` | `d92685165383` | script/gate | [05](05_workflow_validation_and_interfaces.md) |
| 105 | `omega_engine_workflows_agents_skills/application/commands/compile_licensed_term.py` | `15366913faf5` | script/gate | [05](05_workflow_validation_and_interfaces.md) |
| 106 | `omega_engine_workflows_agents_skills/application/commands/compile_projection.py` | `28952d703732` | script/gate | [05](05_workflow_validation_and_interfaces.md) |
| 107 | `omega_engine_workflows_agents_skills/application/commands/verify_catalog.py` | `533bef27d533` | source | [05](05_workflow_validation_and_interfaces.md) |
| 108 | `omega_engine_workflows_agents_skills/application/dtos/__init__.py` | `d122b2cb7872` | package marker | [05](05_workflow_validation_and_interfaces.md) |
| 109 | `omega_engine_workflows_agents_skills/application/dtos/api_error_dto.py` | `4d8fd7d2f9cf` | source | [05](05_workflow_validation_and_interfaces.md) |
| 110 | `omega_engine_workflows_agents_skills/application/dtos/command_dtos.py` | `e05c744a14b4` | source | [05](05_workflow_validation_and_interfaces.md) |
| 111 | `omega_engine_workflows_agents_skills/application/dtos/query_dtos.py` | `f2b2b307506b` | source | [05](05_workflow_validation_and_interfaces.md) |
| 112 | `omega_engine_workflows_agents_skills/application/dtos/success_dtos.py` | `31835f52ea64` | source | [05](05_workflow_validation_and_interfaces.md) |
| 113 | `omega_engine_workflows_agents_skills/application/operad/__init__.py` | `c31ff5389fbf` | package marker | [05](05_workflow_validation_and_interfaces.md) |
| 114 | `omega_engine_workflows_agents_skills/application/operad/budget_service.py` | `c90fafe26446` | source | [05](05_workflow_validation_and_interfaces.md) |
| 115 | `omega_engine_workflows_agents_skills/application/operad/compiler_service.py` | `5378faa2f6b4` | source | [05](05_workflow_validation_and_interfaces.md) |
| 116 | `omega_engine_workflows_agents_skills/application/ports/__init__.py` | `39a938dd1c6a` | package marker | [05](05_workflow_validation_and_interfaces.md) |
| 117 | `omega_engine_workflows_agents_skills/application/ports/clock_port.py` | `f0606e36bb09` | source | [05](05_workflow_validation_and_interfaces.md) |
| 118 | `omega_engine_workflows_agents_skills/application/ports/estate_source_port.py` | `d22495a1dc0b` | source | [05](05_workflow_validation_and_interfaces.md) |
| 119 | `omega_engine_workflows_agents_skills/application/ports/id_generator_port.py` | `feb08a7c0cd4` | source | [05](05_workflow_validation_and_interfaces.md) |
| 120 | `omega_engine_workflows_agents_skills/application/ports/journal_port.py` | `99e2c581850e` | source | [05](05_workflow_validation_and_interfaces.md) |
| 121 | `omega_engine_workflows_agents_skills/application/ports/legacy_catalog_reader_port.py` | `56b4d08846c3` | source | [07](07_migration_legacy_projection_and_custody.md) |
| 122 | `omega_engine_workflows_agents_skills/application/ports/projection_manifest_port.py` | `003ce59cc245` | source | [05](05_workflow_validation_and_interfaces.md) |
| 123 | `omega_engine_workflows_agents_skills/application/ports/skill_document_parser_port.py` | `58fcd13e46a7` | source | [05](05_workflow_validation_and_interfaces.md) |
| 124 | `omega_engine_workflows_agents_skills/application/ports/strict_operad_port.py` | `dca4fdc78716` | source | [05](05_workflow_validation_and_interfaces.md) |
| 125 | `omega_engine_workflows_agents_skills/application/ports/unit_of_work_port.py` | `72b706bf76f2` | source | [05](05_workflow_validation_and_interfaces.md) |
| 126 | `omega_engine_workflows_agents_skills/application/queries/__init__.py` | `a275eb9a65f4` | package marker | [05](05_workflow_validation_and_interfaces.md) |
| 127 | `omega_engine_workflows_agents_skills/application/queries/get_catalog.py` | `ee59e9a9f9bf` | source | [05](05_workflow_validation_and_interfaces.md) |
| 128 | `omega_engine_workflows_agents_skills/application/queries/validate_workflows.py` | `bdc6c0439a1f` | script/gate | [05](05_workflow_validation_and_interfaces.md) |
| 129 | `omega_engine_workflows_agents_skills/controllers/__init__.py` | `3456bf16be05` | package marker | [05](05_workflow_validation_and_interfaces.md) |
| 130 | `omega_engine_workflows_agents_skills/controllers/python_facade.py` | `a000883d6e81` | source | [05](05_workflow_validation_and_interfaces.md) |
| 131 | `omega_engine_workflows_agents_skills/controllers/router.py` | `a760f51e4c7f` | source | [05](05_workflow_validation_and_interfaces.md) |
| 132 | `omega_engine_workflows_agents_skills/controllers/wire_dtos.py` | `b5815a10a8a0` | source | [05](05_workflow_validation_and_interfaces.md) |
| 133 | `omega_engine_workflows_agents_skills/docs/rt/omc_required_changes_0001.md` | `398dcee53926` | document | [12](12_open_issues_nonclaims_and_roadmap.md) |
| 134 | `omega_engine_workflows_agents_skills/domain/__init__.py` | `adba36677a94` | package marker | [05](05_workflow_validation_and_interfaces.md) |
| 135 | `omega_engine_workflows_agents_skills/domain/entities/__init__.py` | `6b5b8ada45a0` | package marker | [02](02_skill_documents_and_ingestion.md) |
| 136 | `omega_engine_workflows_agents_skills/domain/entities/catalog_v3.py` | `51d5889ef540` | source | [02](02_skill_documents_and_ingestion.md) |
| 137 | `omega_engine_workflows_agents_skills/domain/entities/composition_v3.py` | `d85c71998e26` | source | [02](02_skill_documents_and_ingestion.md) |
| 138 | `omega_engine_workflows_agents_skills/domain/entities/operation_v3.py` | `85b6dfa933cb` | source | [02](02_skill_documents_and_ingestion.md) |
| 139 | `omega_engine_workflows_agents_skills/domain/entities/skill_document_v3.py` | `4f0d831c06da` | source | [02](02_skill_documents_and_ingestion.md) |
| 140 | `omega_engine_workflows_agents_skills/domain/errors/__init__.py` | `16ba45b34a25` | package marker | [05](05_workflow_validation_and_interfaces.md) |
| 141 | `omega_engine_workflows_agents_skills/domain/errors/domain_errors.py` | `d9db7130876a` | source | [05](05_workflow_validation_and_interfaces.md) |
| 142 | `omega_engine_workflows_agents_skills/domain/events/__init__.py` | `15920b82bc54` | package marker | [05](05_workflow_validation_and_interfaces.md) |
| 143 | `omega_engine_workflows_agents_skills/domain/events/domain_events.py` | `9b04255d2e56` | source | [05](05_workflow_validation_and_interfaces.md) |
| 144 | `omega_engine_workflows_agents_skills/domain/operad/__init__.py` | `cc078a933bb2` | package marker | [03](03_colours_operations_and_composition.md) |
| 145 | `omega_engine_workflows_agents_skills/domain/operad/colours.py` | `a5935f520ccb` | source | [03](03_colours_operations_and_composition.md) |
| 146 | `omega_engine_workflows_agents_skills/domain/operad/errors.py` | `e16d74f8a6a7` | source | [03](03_colours_operations_and_composition.md) |
| 147 | `omega_engine_workflows_agents_skills/domain/operad/evidence.py` | `60cd1d16145e` | source | [03](03_colours_operations_and_composition.md) |
| 148 | `omega_engine_workflows_agents_skills/domain/operad/operad.py` | `2e68c5cd06d3` | source | [03](03_colours_operations_and_composition.md) |
| 149 | `omega_engine_workflows_agents_skills/domain/operad/operation.py` | `a132ef470a90` | source | [03](03_colours_operations_and_composition.md) |
| 150 | `omega_engine_workflows_agents_skills/domain/operad/planar.py` | `fb5696fd7aec` | source | [03](03_colours_operations_and_composition.md) |
| 151 | `omega_engine_workflows_agents_skills/domain/value_objects/__init__.py` | `12afd2326630` | package marker | [02](02_skill_documents_and_ingestion.md) |
| 152 | `omega_engine_workflows_agents_skills/domain/value_objects/authority.py` | `7be6419d7a3b` | source | [02](02_skill_documents_and_ingestion.md) |
| 153 | `omega_engine_workflows_agents_skills/domain/value_objects/byte_span.py` | `3f01d998b5bf` | source | [02](02_skill_documents_and_ingestion.md) |
| 154 | `omega_engine_workflows_agents_skills/domain/value_objects/content_digest.py` | `986fac050806` | source | [02](02_skill_documents_and_ingestion.md) |
| 155 | `omega_engine_workflows_agents_skills/domain/value_objects/identifier.py` | `dc48dd951594` | source | [02](02_skill_documents_and_ingestion.md) |
| 156 | `omega_engine_workflows_agents_skills/domain/value_objects/lifecycle_facets.py` | `393b7c3eeec4` | source | [02](02_skill_documents_and_ingestion.md) |
| 157 | `omega_engine_workflows_agents_skills/domain/value_objects/operands.py` | `5d7ba94d253d` | source | [02](02_skill_documents_and_ingestion.md) |
| 158 | `omega_engine_workflows_agents_skills/frontend/__init__.py` | `2afebf2fc8f3` | package marker | [05](05_workflow_validation_and_interfaces.md) |
| 159 | `omega_engine_workflows_agents_skills/frontend/api/__init__.py` | `a364fa610753` | package marker | [05](05_workflow_validation_and_interfaces.md) |
| 160 | `omega_engine_workflows_agents_skills/frontend/api/app.py` | `ffcedb8d03ad` | source | [05](05_workflow_validation_and_interfaces.md) |
| 161 | `omega_engine_workflows_agents_skills/frontend/cli/__init__.py` | `70ea6f7466ba` | package marker | [05](05_workflow_validation_and_interfaces.md) |
| 162 | `omega_engine_workflows_agents_skills/frontend/cli/__main__.py` | `481b56e6d095` | source | [05](05_workflow_validation_and_interfaces.md) |
| 163 | `omega_engine_workflows_agents_skills/frontend/cli/main.py` | `5c325196c7a6` | source | [05](05_workflow_validation_and_interfaces.md) |
| 164 | `omega_engine_workflows_agents_skills/frontend/cli/operad_cli.py` | `850e074d17af` | source | [05](05_workflow_validation_and_interfaces.md) |
| 165 | `omega_engine_workflows_agents_skills/infrastructure/__init__.py` | `418fb9141fda` | package marker | [05](05_workflow_validation_and_interfaces.md) |
| 166 | `omega_engine_workflows_agents_skills/infrastructure/bootstrap.py` | `9afa8b4d0212` | source | [05](05_workflow_validation_and_interfaces.md) |
| 167 | `omega_engine_workflows_agents_skills/infrastructure/fs/fs_estate_source_adapter.py` | `cbc45dcdb3c7` | source | [05](05_workflow_validation_and_interfaces.md) |
| 168 | `omega_engine_workflows_agents_skills/infrastructure/fs/legacy_catalog_reader_adapter.py` | `a2eebe1e6d0b` | source | [07](07_migration_legacy_projection_and_custody.md) |
| 169 | `omega_engine_workflows_agents_skills/infrastructure/fs_reader.py` | `4b6df1e98910` | source | [05](05_workflow_validation_and_interfaces.md) |
| 170 | `omega_engine_workflows_agents_skills/infrastructure/legacy/catalog_v2.py` | `81467750fd33` | source | [07](07_migration_legacy_projection_and_custody.md) |
| 171 | `omega_engine_workflows_agents_skills/infrastructure/legacy/interfaces.py` | `d6f26f708712` | source | [07](07_migration_legacy_projection_and_custody.md) |
| 172 | `omega_engine_workflows_agents_skills/infrastructure/legacy/models.py` | `286824e6c670` | source | [07](07_migration_legacy_projection_and_custody.md) |
| 173 | `omega_engine_workflows_agents_skills/infrastructure/legacy/use_cases/__init__.py` | `fdbdeaf01bac` | package marker | [07](07_migration_legacy_projection_and_custody.md) |
| 174 | `omega_engine_workflows_agents_skills/infrastructure/legacy/use_cases/compile_catalog_v2.py` | `bfa624e8383a` | script/gate | [07](07_migration_legacy_projection_and_custody.md) |
| 175 | `omega_engine_workflows_agents_skills/infrastructure/legacy/use_cases/compile_operad_terms.py` | `7ba0b14def39` | script/gate | [07](07_migration_legacy_projection_and_custody.md) |
| 176 | `omega_engine_workflows_agents_skills/infrastructure/legacy/use_cases/parse_estate.py` | `b42b514a062d` | source | [07](07_migration_legacy_projection_and_custody.md) |
| 177 | `omega_engine_workflows_agents_skills/infrastructure/legacy/use_cases/validate_workflows.py` | `957f84b23361` | script/gate | [07](07_migration_legacy_projection_and_custody.md) |
| 178 | `omega_engine_workflows_agents_skills/infrastructure/legacy/use_cases/woland_projection.py` | `5e883a223c16` | source | [07](07_migration_legacy_projection_and_custody.md) |
| 179 | `omega_engine_workflows_agents_skills/infrastructure/operad/higher_operad_adapter.py` | `24222639640d` | source | [05](05_workflow_validation_and_interfaces.md) |
| 180 | `omega_engine_workflows_agents_skills/infrastructure/parser/markdown_parser_adapter.py` | `ad82a7aef43a` | source | [05](05_workflow_validation_and_interfaces.md) |
| 181 | `omega_engine_workflows_agents_skills/infrastructure/providers/manifest_signature_provider.py` | `05437d15eb50` | source | [05](05_workflow_validation_and_interfaces.md) |
| 182 | `omega_engine_workflows_agents_skills/infrastructure/providers/projection_manifest_adapter.py` | `7c20db7fad57` | source | [05](05_workflow_validation_and_interfaces.md) |
| 183 | `omega_engine_workflows_agents_skills/infrastructure/providers/system_clock.py` | `09b5113ec255` | source | [05](05_workflow_validation_and_interfaces.md) |
| 184 | `omega_engine_workflows_agents_skills/infrastructure/providers/uuid_id_generator.py` | `cd6fbfc9376b` | source | [05](05_workflow_validation_and_interfaces.md) |
| 185 | `omega_engine_workflows_agents_skills/infrastructure/storage/outbox_dispatcher.py` | `785f3872b687` | source | [06](06_persistence_provenance_security_and_receipts.md) |
| 186 | `omega_engine_workflows_agents_skills/infrastructure/storage/sqlite_unit_of_work.py` | `50a6007aaac8` | source | [06](06_persistence_provenance_security_and_receipts.md) |
| 187 | `omega_engine_workflows_agents_skills/manifests/woland_engineering_v1.json` | `897190ee0216` | manifest/data | [07](07_migration_legacy_projection_and_custody.md) |
| 188 | `omega_engine_workflows_agents_skills/migration/__init__.py` | `840f17c7be68` | package marker | [07](07_migration_legacy_projection_and_custody.md) |
| 189 | `omega_engine_workflows_agents_skills/migration/migration_manifest_v3.json` | `ef9db1e03c51` | manifest/data | [07](07_migration_legacy_projection_and_custody.md) |
| 190 | `omega_engine_workflows_agents_skills/migration/refresh_migration_manifest.py` | `acc7788f0763` | script/gate | [07](07_migration_legacy_projection_and_custody.md) |
| 191 | `omega_engine_workflows_agents_skills/migration/skill_migrator.py` | `a095212e7cbf` | source | [07](07_migration_legacy_projection_and_custody.md) |
| 192 | `omega_engine_workflows_agents_skills/tests/__init__.py` | `a22b00b81772` | test | [09](09_testing_and_falsification.md) |
| 193 | `omega_engine_workflows_agents_skills/tests/architecture/__init__.py` | `605703661773` | test | [09](09_testing_and_falsification.md) |
| 194 | `omega_engine_workflows_agents_skills/tests/architecture/test_clean_architecture_ast_boundaries.py` | `c94307dae9e9` | test | [09](09_testing_and_falsification.md) |
| 195 | `omega_engine_workflows_agents_skills/tests/contract/__init__.py` | `605703661773` | test | [09](09_testing_and_falsification.md) |
| 196 | `omega_engine_workflows_agents_skills/tests/contract/test_fastapi_router_contracts.py` | `7ec6b3a957f5` | test | [09](09_testing_and_falsification.md) |
| 197 | `omega_engine_workflows_agents_skills/tests/contract/test_oewas_python_facade.py` | `a2b4af609eab` | test | [09](09_testing_and_falsification.md) |
| 198 | `omega_engine_workflows_agents_skills/tests/integration/__init__.py` | `605703661773` | test | [09](09_testing_and_falsification.md) |
| 199 | `omega_engine_workflows_agents_skills/tests/integration/test_agent_to_agent_dag_compilation.py` | `7ffad8608857` | test | [09](09_testing_and_falsification.md) |
| 200 | `omega_engine_workflows_agents_skills/tests/integration/test_asgi_multi_tenant_compile_catalog.py` | `ed2eebbab5e2` | test | [09](09_testing_and_falsification.md) |
| 201 | `omega_engine_workflows_agents_skills/tests/integration/test_benchmark_burst_load.py` | `f41918976219` | test | [09](09_testing_and_falsification.md) |
| 202 | `omega_engine_workflows_agents_skills/tests/integration/test_cli_frontend_encoding_and_exit_codes.py` | `a5ad00509292` | test | [09](09_testing_and_falsification.md) |
| 203 | `omega_engine_workflows_agents_skills/tests/integration/test_concurrent_multi_worker_idempotency.py` | `940ffe0f2c19` | test | [09](09_testing_and_falsification.md) |
| 204 | `omega_engine_workflows_agents_skills/tests/integration/test_dual_read_legacy_catalog.py` | `6c0c4c8ae021` | test | [09](09_testing_and_falsification.md) |
| 205 | `omega_engine_workflows_agents_skills/tests/integration/test_e2e_full_lifecycle_roundtrip.py` | `6afee3d19d22` | test | [09](09_testing_and_falsification.md) |
| 206 | `omega_engine_workflows_agents_skills/tests/integration/test_e2e_multi_stage_agentic_terms.py` | `97dd1eafceae` | test | [09](09_testing_and_falsification.md) |
| 207 | `omega_engine_workflows_agents_skills/tests/integration/test_e2e_schema_migration_lossless.py` | `6350414bd874` | test | [09](09_testing_and_falsification.md) |
| 208 | `omega_engine_workflows_agents_skills/tests/integration/test_goo_migration_manifest_parity.py` | `11e53156a580` | test | [09](09_testing_and_falsification.md) |
| 209 | `omega_engine_workflows_agents_skills/tests/integration/test_higher_operad_adapter.py` | `5ad62b13792a` | test | [09](09_testing_and_falsification.md) |
| 210 | `omega_engine_workflows_agents_skills/tests/integration/test_higher_operad_laws_and_cyclic_graphs.py` | `3268b1710ebe` | test | [09](09_testing_and_falsification.md) |
| 211 | `omega_engine_workflows_agents_skills/tests/integration/test_legacy_woland_projection.py` | `d3191e72ea4a` | test | [09](09_testing_and_falsification.md) |
| 212 | `omega_engine_workflows_agents_skills/tests/integration/test_manifest_signature_adversarial_matrix.py` | `ecb1cf66b80e` | test | [09](09_testing_and_falsification.md) |
| 213 | `omega_engine_workflows_agents_skills/tests/integration/test_openapi_schema_and_swagger_docs.py` | `2a26dbceb1e9` | test | [09](09_testing_and_falsification.md) |
| 214 | `omega_engine_workflows_agents_skills/tests/integration/test_outbox_message_dispatcher.py` | `2cdf90c8a19d` | test | [09](09_testing_and_falsification.md) |
| 215 | `omega_engine_workflows_agents_skills/tests/integration/test_outbox_transaction_atomicity.py` | `963e4ea22af8` | test | [09](09_testing_and_falsification.md) |
| 216 | `omega_engine_workflows_agents_skills/tests/integration/test_projection_manifest_signature_verification.py` | `dffd18e3f685` | test | [09](09_testing_and_falsification.md) |
| 217 | `omega_engine_workflows_agents_skills/tests/integration/test_sql_constraint_rejection_matrix.py` | `f1904ef0e3b8` | test | [09](09_testing_and_falsification.md) |
| 218 | `omega_engine_workflows_agents_skills/tests/integration/test_sqlite_journal_unit_of_work.py` | `6a396e416a4a` | test | [09](09_testing_and_falsification.md) |
| 219 | `omega_engine_workflows_agents_skills/tests/unit/__init__.py` | `605703661773` | test | [09](09_testing_and_falsification.md) |
| 220 | `omega_engine_workflows_agents_skills/tests/unit/test_application_railway_handlers.py` | `0820bf275ad7` | test | [09](09_testing_and_falsification.md) |
| 221 | `omega_engine_workflows_agents_skills/tests/unit/test_domain_value_objects.py` | `265a7b526b3e` | test | [09](09_testing_and_falsification.md) |
| 222 | `omega_engine_workflows_agents_skills/tests/unit/test_domain_value_objects_boundary_and_fuzz.py` | `662e88fdf98d` | test | [09](09_testing_and_falsification.md) |
| 223 | `omega_engine_workflows_agents_skills/tests/unit/test_lossless_markdown_parser.py` | `5c4feb2e5f98` | test | [09](09_testing_and_falsification.md) |
| 224 | `omega_engine_workflows_agents_skills/tests/unit/test_markdown_parser_edge_case_fuzz.py` | `45237958dbcd` | test | [09](09_testing_and_falsification.md) |
| 225 | `omega_engine_workflows_agents_skills/tests/unit/test_markdown_parser_property_laws.py` | `5184c5360293` | test | [09](09_testing_and_falsification.md) |
| 226 | `omega_engine_workflows_agents_skills/tests/unit/test_operad_clean_arch.py` | `038696f6edfe` | test | [09](09_testing_and_falsification.md) |
| 227 | `omega_engine_workflows_agents_skills/tests/unit/test_operad_colour_vocabulary.py` | `ab02d69d88ae` | test | [09](09_testing_and_falsification.md) |
| 228 | `omega_engine_workflows_agents_skills/tests/unit/test_operad_compile_receipt.py` | `b78601f36ca5` | test | [09](09_testing_and_falsification.md) |
| 229 | `omega_engine_workflows_agents_skills/tests/unit/test_operad_compiler_service.py` | `fba60ef09091` | test | [09](09_testing_and_falsification.md) |
| 230 | `omega_engine_workflows_agents_skills/tests/unit/test_prompt_civilization_oewas.py` | `4331b646b75b` | test | [09](09_testing_and_falsification.md) |
| 231 | `omega_engine_workflows_agents_skills/tests/unit/test_skill_document_v3_aggregate.py` | `1ca2c5bad4ad` | test | [09](09_testing_and_falsification.md) |

## Reconciliation totals

The table above is generated from the Git tree, then committed as static review
evidence. Validation must compare its path set and blob prefixes back to the frozen
Git tree. A missing, duplicated, extra, or mismatched row is a coverage failure.
