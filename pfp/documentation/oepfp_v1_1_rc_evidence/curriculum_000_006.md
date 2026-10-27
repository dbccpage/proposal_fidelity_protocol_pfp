> Source-attributed audit appendix. Source and original-extraction hashes quoted below are distinct from the wrapped release artifact hashes recorded in source_manifest.json. Historical verdicts and quoted terminology are retained as evidence; no estate test or model call was executed by this extraction. Full machine extraction: [curriculum_000_006.json.gz](curriculum_000_006.json.gz).

# Curriculum000–006 forensic source synthesis

Snapshot: `58a6a1ef92e155b1fa3783081becb41de3e07734` in `/workspace/the_symbol_game`. AuthorityEffect: None.

This is a byte-complete inventory of the seven current track directories and a source-only mathematical audit. The companion JSON records every file, SHA256, type, headings, matched mathematical/status passages, Python/Lean/Rust declarations, grammar productions, notebook source/stored-output metadata, normal-form contract fields, unresolved local-link candidates and referenced executable sources. Matching text indexes a candidate claim; it does not verify that claim. No Cargo, pytest, Lean build, notebook, grammar checker or provider call ran for this audit. Stored historical PASS/status text is attributed evidence only.

An exhaustive path census is not an exhaustive line-by-line mathematical proof audit. The concise thematic findings below prioritize source-defined primitives, conditional identities, owner boundaries and contradictions relevant to the requested v1.1RC architecture. The full source declarations/passages remain available in JSON for every file.

## Census

| Track | Files | Python | Lean | Rust | SQL | Notebooks | Contract/schema YAML in normal-form folders |
|---|---:|---:|---:|---:|---:|---:|---:|
| 000_oepregen | 17 | 2 | 0 | 0 | 0 | 0 | 0 |
| 001_oegen | 155 | 38 | 21 | 0 | 0 | 0 | 15 |
| 002_oesn | 95 | 15 | 4 | 0 | 0 | 0 | 9 |
| 003_oemssn | 346 | 92 | 25 | 24 | 14 | 0 | 13 |
| 004_oepfp | 1277 | 23 | 1 | 0 | 0 | 200 | 0 |
| 005_oegenong | 77 | 1 | 0 | 0 | 0 | 3 | 6 |
| 006_oewdp | 329 | 17 | 5 | 0 | 0 | 41 | 28 |

Total: 2296 files. Track005 is present as **005_oegenong (Genesis Ongoing)**, despite its omission from the prompt's primary track list. The cross-reference census contains 1329 existing executable/formal files; references alone are not verified ownership or call-graph evidence. The scanner found 1030 unresolved local-path candidates; these include historical renamed paths and should be checked individually rather than promoted into a complete broken-link verdict.

## 000_oepregen

### Definitions and identities

- Opaque inscriptions and supplied observations are separate. Observational equivalence x≈_O y means every supplied observation agrees; O=∅ collapses every pair. A task separating two collapsed inputs cannot factor through their common quotient. [education/documentation/000_oepregen/03_results_and_arguments.md:64](../../../education/documentation/000_oepregen/03_results_and_arguments.md#L64) [education/documentation/000_oepregen/03_results_and_arguments.md:75](../../../education/documentation/000_oepregen/03_results_and_arguments.md#L75)

- Replay obstruction: π(h1)=π(h2) with σ(h1)≠σ(h2) forbids an auditor A with Aπ=σ on every history. A sufficient summary exists exactly when σ is constant on each π-fiber; preserving full raw history is a separate provenance choice. [education/documentation/000_oepregen/03_results_and_arguments.md:100](../../../education/documentation/000_oepregen/03_results_and_arguments.md#L100) [education/documentation/000_oepregen/03_results_and_arguments.md:115](../../../education/documentation/000_oepregen/03_results_and_arguments.md#L115)

- No-transition quiescence follows from an empty transition relation. Repetition/self-loops require an additional declared rule; neither <> nor a presentation change forces a canonical successor. [education/documentation/000_oepregen/03_results_and_arguments.md:23](../../../education/documentation/000_oepregen/03_results_and_arguments.md#L23) [education/documentation/000_oepregen/03_results_and_arguments.md:58](../../../education/documentation/000_oepregen/03_results_and_arguments.md#L58)

### Transition and normal-form boundary

- Grammar public starts are ground_token, inscription and pre_genesis_regime; absent input, empty word, literal <> and host list {} are separate cases. The grammar has no transition semantics. [education/documentation/000_oepregen/grammar/README.md:21](../../../education/documentation/000_oepregen/grammar/README.md#L21) [education/documentation/000_oepregen/grammar/README.md:30](../../../education/documentation/000_oepregen/grammar/README.md#L30)

- PG1–PG8 rewriting, refusal packets and error labels are prose specifications. The grammar checker only loads declared EBNF cases and compares accept/refuse results; it does not execute those eight strategies. [education/documentation/000_oepregen/rewriting/rewriting_strategies_pregen_wire.md:206](../../../education/documentation/000_oepregen/rewriting/rewriting_strategies_pregen_wire.md#L206) [education/documentation/000_oepregen/code/check_pre_genesis.py:102](../../../education/documentation/000_oepregen/code/check_pre_genesis.py#L102)

### Executable and formal owners

- Present executable owner: check_pre_genesis.py uses Track004 grammar/check_grammars.py Grammar. This audit inspected that call but executed no checker or tests. [education/documentation/000_oepregen/code/check_pre_genesis.py:38](../../../education/documentation/000_oepregen/code/check_pre_genesis.py#L38)

- README reports three runs, no general performance rates, and no host check of model replies. Source status is an attributed historical account, not a new benchmark receipt. [education/documentation/000_oepregen/README.md:68](../../../education/documentation/000_oepregen/README.md#L68) [education/documentation/000_oepregen/README.md:86](../../../education/documentation/000_oepregen/README.md#L86)

### Forensic findings

- Availability mismatch: sources/README.md claims six primary record files, but only README.md, design_derivation_v0.md and analysis_derivation_v1.md are present in this checkout. The four named transcript/prompt-pack files are absent, so current source citations to them cannot be independently read here. [education/documentation/000_oepregen/sources/README.md:5](../../../education/documentation/000_oepregen/sources/README.md#L5)

- Internal scope conflict: the corrected results allow sufficient summaries, while PG7 asserts full sequential history is required by replay necessity. Preserve this as an inconsistency to resolve; the theorem only requires enough retained information to distinguish required answers. [education/documentation/000_oepregen/rewriting/rewriting_strategies_pregen_wire.md:294](../../../education/documentation/000_oepregen/rewriting/rewriting_strategies_pregen_wire.md#L294) [education/documentation/000_oepregen/03_results_and_arguments.md:115](../../../education/documentation/000_oepregen/03_results_and_arguments.md#L115)

Normal-form artifact paths and complete field excerpts are in `tracks[].normal_form_contract_inventory`; all lesson pages appear in `level_pages`, including their exact source headings.

## 001_oegen

### Definitions and identities

- The 19 selected educational families are seed/admission/regime; primitive difference/pointed carriers; passage/active obstruction; refusal/boundary; simplicial boundary; transition alphabet; derivation trees; apartness; contact; attachment filtration; renaming; observer profiles; presentation frames; controller grammars; trace algebra; stable content; weight rays; represented progress; endogenous fidelity. They are selected models, not an exhaustive derivation from one glyph. [education/documentation/001_oegen/levels/README.md:41](../../../education/documentation/001_oegen/levels/README.md#L41) [education/documentation/001_oegen/primitives/README.md:22](../../../education/documentation/001_oegen/primitives/README.md#L22)

- Supply is not admission. Declared regime R=(D,F,I,U,Q) keeps datum, form, instance and protected-pair information. An asserted relation only separates endpoints after witness and irreflexivity assumptions are supplied; bare typography does not supply them. [education/documentation/001_oegen/levels/README.md:12](../../../education/documentation/001_oegen/levels/README.md#L12) [education/documentation/001_oegen/primitives/README.md:40](../../../education/documentation/001_oegen/primitives/README.md#L40)

- Other indexed constructions include declared apartness (irreflexivity/symmetry/cotransitivity), negated-apartness equivalence, pointed relation morphisms preserving designated endpoints and arrows, finite permutation orbits, commuting independent trace events, exact integer ray cross-products and alternating simplicial boundary cancellation. [education/documentation/001_oegen/primitives/lean4/PrimitiveDifference.lean:88](../../../education/documentation/001_oegen/primitives/lean4/PrimitiveDifference.lean#L88) [education/documentation/001_oegen/primitives/README.md:63](../../../education/documentation/001_oegen/primitives/README.md#L63) [education/documentation/001_oegen/primitives/primitives_monograph.md:63](../../../education/documentation/001_oegen/primitives/primitives_monograph.md#L63)

### Transition and normal-form boundary

- Teaching Levels00–100 are 33 nonconsecutive lesson identifiers, not S(n) stages or a uniformly sealed theorem population. Event forms include supply/admit datum/form/instance; later passage/trace repair and extension grammars have separate assumptions and source pins. [education/documentation/001_oegen/levels/README.md:3](../../../education/documentation/001_oegen/levels/README.md#L3) [education/documentation/001_oegen/README.md:48](../../../education/documentation/001_oegen/README.md#L48)

- Fourteen nf.* contracts plus one schema are present: AONF/APNF/IGNF/IRNF/LSNF/OBNF/PDNF/RPNF, authority, EFNF/ENF, observer, evidence provenance and MTNF. All names, fields, statuses and invariant passages are indexed in the JSON. Sample contracts are draft extended forms with qualifies_as_true_normal_form:false; a title is not an executed normalization proof. [education/documentation/001_oegen/normal_forms/nf.derivation.irnf.yaml:9](../../../education/documentation/001_oegen/normal_forms/nf.derivation.irnf.yaml#L9) [education/documentation/001_oegen/normal_forms/nf.derivation.irnf.yaml:41](../../../education/documentation/001_oegen/normal_forms/nf.derivation.irnf.yaml#L41)

### Executable and formal owners

- Present local executable/formal estate:38Python and21Lean files (including tests/build/audit helpers). Primitives use finite educational dataclasses/helpers; grammar delegates to Track004 Grammar. Native reusable owners are explicitly separated from WDP source binding. [education/documentation/001_oegen/code/check_genesis.py:31](../../../education/documentation/001_oegen/code/check_genesis.py#L31) [education/documentation/001_oegen/wdp_integration.md:59](../../../education/documentation/001_oegen/wdp_integration.md#L59)

- Actual native owner sources located include core_wdp difference, genesis admission/source execution/translation; core_homology cochain/simplicial; core_holonomy signed_transport; core_category_theory finite_report_descent; core_quantum_physics signed_sampling. Presence and source references do not establish that every lesson dynamically calls them. [education/documentation/006_oewdp/levels/level_23_sovereign_difference_grounding.md:51](../../../education/documentation/006_oewdp/levels/level_23_sovereign_difference_grounding.md#L51) [education/documentation/001_oegen/wdp_integration.md:61](../../../education/documentation/001_oegen/wdp_integration.md#L61)

### Forensic findings

- README withdraws prior complete-extraction and blanket advanced-verification claims. The old monograph still contains historical SEALED and contextuality/Regge language; use per-notion corrected scope, not its taxonomy labels as proof status. [education/documentation/001_oegen/README.md:40](../../../education/documentation/001_oegen/README.md#L40) [education/documentation/001_oegen/primitives/README.md:24](../../../education/documentation/001_oegen/primitives/README.md#L24)

Normal-form artifact paths and complete field excerpts are in `tracks[].normal_form_contract_inventory`; all lesson pages appear in `level_pages`, including their exact source headings.

## 002_oesn

### Definitions and identities

- S(n) labels declared presentations. S0 is an empty admitted regime with opaque supplied <>; S1 supply alone is a no-op; S2 retention/collapse differs from a pair parser; S3 separation costs depend on item and arity grammar; S4 closure needs a specified policy; S5 a continuation request is input; S6 is a later section/partial-inverse construction. [education/documentation/002_oesn/sn.md:34](../../../education/documentation/002_oesn/sn.md#L34) [education/documentation/002_oesn/source_correspondence.md:22](../../../education/documentation/002_oesn/source_correspondence.md#L22)

- Under supplied irreflexivity R(a,b)⇒a≠b and support cardinality2. This endpoint count is separate from witness multiplicity or admission cost. Refinement q′(x)=(q(x),t(x)) retains q by first projection; multiple conflict pairs require a declared graph coloring problem. [education/documentation/002_oesn/sn.md:65](../../../education/documentation/002_oesn/sn.md#L65) [education/documentation/002_oesn/sn.md:76](../../../education/documentation/002_oesn/sn.md#L76)

- Exact recovery uses an injection u and a partial inverse on its actual image, returning NON_DESCENT outside it. r̂(u(x))=inl(x) does not by itself prove an adjunction or future transition commutation. [education/documentation/002_oesn/sn.md:87](../../../education/documentation/002_oesn/sn.md#L87) [education/documentation/002_oesn/sn.md:98](../../../education/documentation/002_oesn/sn.md#L98)

- Survivor bookkeeping is W′=(W minus D)⊔B and |W′|=|W|−|D|+|B| under subset/disjointness premises. Persistent receipt sets and ordered event histories differ. Construction depth n is independent of Postnikov depth j; fixed-space Postnikov truncation preserves π0. [education/documentation/002_oesn/sn.md:118](../../../education/documentation/002_oesn/sn.md#L118) [education/documentation/002_oesn/sn.md:107](../../../education/documentation/002_oesn/sn.md#L107)

### Transition and normal-form boundary

- Eight draft nf.* contracts cover PDNF,RPNF,SCNF,SERNF,OBNF,NAR-NF,state and provenance, plus a schema. Full contract verifiers are not executed by YAML shape validation. [education/documentation/002_oesn/source_correspondence.md:49](../../../education/documentation/002_oesn/source_correspondence.md#L49)

### Executable and formal owners

- Local sn_core, sn_realizations, sn_applications, sn_verification, sn_codec and sn_audit implement declared finite examples, codecs and local monitors. Grammar checks85cases. Lean SnSyntax/SnCarrier/SnTheorems prove their typed syntax, chosen carrier table and old-image facts, without parser parity or a forced unique Genesis history. [education/documentation/002_oesn/code/README.md:5](../../../education/documentation/002_oesn/code/README.md#L5) [education/documentation/002_oesn/source_correspondence.md:44](../../../education/documentation/002_oesn/source_correspondence.md#L44) [education/documentation/002_oesn/source_correspondence.md:67](../../../education/documentation/002_oesn/source_correspondence.md#L67)

### Forensic findings

- Legacy names AdjunctionCochain.verify_counit and DiscreteHodge.verify_dimension_sum denote only a section/retraction check and integer arithmetic; they are not general adjunction or Hodge solvers. Domain FIFO/Regge specifications are richer than local toy implementations. [education/documentation/002_oesn/code/README.md:21](../../../education/documentation/002_oesn/code/README.md#L21) [education/documentation/002_oesn/source_correspondence.md:42](../../../education/documentation/002_oesn/source_correspondence.md#L42)

Normal-form artifact paths and complete field excerpts are in `tracks[].normal_form_contract_inventory`; all lesson pages appear in `level_pages`, including their exact source headings.

## 003_oemssn

### Definitions and identities

- MSS-N is an external atlas of101 proposed capability specifications. Genesis source index, S(n) presentation index and MSS atlas index are independent; no licensed chain MSS0→MSS100 is established. [education/documentation/003_oemssn/README.md:18](../../../education/documentation/003_oemssn/README.md#L18) [education/documentation/003_oemssn/README.md:52](../../../education/documentation/003_oemssn/README.md#L52)

- Declared Γ38 comprises lowercase Latin letters, digits and angle glyphs. Alphabet inclusion extends to an injective free-monoid map with partial decoder r(u(w))=w. Free monoids of distinct finite ranks are nonisomorphic despite countable underlying sets. Countable alphabet x_k↦1^k0 gives a prefix-free injective encoding; its exact image is ε plus binary words ending in0. [education/documentation/003_oemssn/levels/level_insert_38_symbol_ladder_and_transfinite_forms.md:40](../../../education/documentation/003_oemssn/levels/level_insert_38_symbol_ladder_and_transfinite_forms.md#L40) [education/documentation/003_oemssn/levels/level_insert_38_symbol_ladder_and_transfinite_forms.md:74](../../../education/documentation/003_oemssn/levels/level_insert_38_symbol_ladder_and_transfinite_forms.md#L74) [education/documentation/003_oemssn/levels/level_insert_38_symbol_ladder_and_transfinite_forms.md:100](../../../education/documentation/003_oemssn/levels/level_insert_38_symbol_ladder_and_transfinite_forms.md#L100)

- Concrete formal source separates Boolean four-gate obstruction factorization, integer cycle circulation,2×2 commutator trace, group-derived pure-gauge triangle cancellation and checks on supplied Smith factors. No general Bianchi/Regge identity, Smith reduction, teleportation fidelity or anyon-coherence theorem follows. [education/documentation/003_oemssn/lean4/README.md:11](../../../education/documentation/003_oemssn/lean4/README.md#L11) [education/documentation/003_oemssn/lean4/README.md:13](../../../education/documentation/003_oemssn/lean4/README.md#L13) [education/documentation/003_oemssn/lean4/README.md:15](../../../education/documentation/003_oemssn/lean4/README.md#L15)

### Transition and normal-form boundary

- The22public grammar starts, proposed mss-boundary-v1 packets and binary executable tower wire are distinct syntaxes. Proposed Evaluator::* and ERR_* labels do not establish implemented runtime handlers. Old-word preservation is weaker than preservation of meaning under noninjective substitution retractions. [education/documentation/003_oemssn/README.md:67](../../../education/documentation/003_oemssn/README.md#L67) [education/documentation/003_oemssn/README.md:71](../../../education/documentation/003_oemssn/README.md#L71) [education/documentation/003_oemssn/publication_review.md:32](../../../education/documentation/003_oemssn/publication_review.md#L32)

- Twelve nf.* YAML artifacts plus schema are indexed across track/domain folders: cochain Hodge, CODA simplex, OBNF,SCNF,DDANF,BQNF,MSSN,alternation-safe recursion,DBCNF,GNF,TBNF,ZFNF. They are declarations with file-specific statuses; the grammar cannot execute their whole semantic obligations. [education/documentation/003_oemssn/normal_forms/nf.mssn.yaml:54](../../../education/documentation/003_oemssn/normal_forms/nf.mssn.yaml#L54)

### Executable and formal owners

- Present executable/formal population includes92Python,25Lean,24Rust and14SQL files across domain examples. Core codecs/check_mssn handle22starts/39storedcases; six top-level Lean modules have distinct limited scopes. Historical October9 direct Lean4.33.1 and targeted domain-test evidence is stated, while full pinned4.34Lake and full estate proofs were not rerun. [education/documentation/003_oemssn/publication_review.md:14](../../../education/documentation/003_oemssn/publication_review.md#L14) [education/documentation/003_oemssn/lean4/README.md:17](../../../education/documentation/003_oemssn/lean4/README.md#L17) [education/documentation/003_oemssn/publication_review.md:70](../../../education/documentation/003_oemssn/publication_review.md#L70)

### Forensic findings

- The publication review explicitly rejects blanket verification of all101MSS rows. Domain fixed-root recovery-gap predicates were corrected to singleton conditions with witnessed-pair counterexamples; physical-emergence and automatic continuum claims must remain separated from those actual statements. [education/documentation/003_oemssn/publication_review.md:6](../../../education/documentation/003_oemssn/publication_review.md#L6) [education/documentation/003_oemssn/publication_review.md:44](../../../education/documentation/003_oemssn/publication_review.md#L44)

Normal-form artifact paths and complete field excerpts are in `tracks[].normal_form_contract_inventory`; all lesson pages appear in `level_pages`, including their exact source headings.

## 004_oepfp

### Definitions and identities

- Minimal executable context C=(X,Q,check,R) uses finite named obligations, partial licensed repairs and Pass/Fail(w)/Unknown(r). Ω_C is the failed-obligation map, not an intrinsic numeric norm; acceptance additionally requires every check Pass, so Unknown cannot disappear merely because Ω is empty. [education/documentation/004_oepfp/math/02_executable_contexts_and_reachability.md:19](../../../education/documentation/004_oepfp/math/02_executable_contexts_and_reachability.md#L19) [education/documentation/004_oepfp/math/02_executable_contexts_and_reachability.md:38](../../../education/documentation/004_oepfp/math/02_executable_contexts_and_reachability.md#L38)

- R1 same-context repair has priority. Structural exhaustion universally excludes an accepted state from the reflexive-transitive reachable closure and requires complete finite coverage or a completeness theorem; timeout is Unknown. R2 licenses assessing declared conservative extensions, not an automatic unique least lift. [education/documentation/004_oepfp/math/02_executable_contexts_and_reachability.md:81](../../../education/documentation/004_oepfp/math/02_executable_contexts_and_reachability.md#L81) [education/documentation/004_oepfp/math/07_mathematical_obligations_register.yaml:106](../../../education/documentation/004_oepfp/math/07_mathematical_obligations_register.yaml#L106)

- A conservative extension declares C,C′,embedding,partial forget map,structure delta and justification. Old typing/judgment preservation and reflection, protected questions and forget-after-lift must be checked separately; a retraction alone is not general semantic conservativity. [education/documentation/004_oepfp/math/04_conservative_context_extension_and_descent.md:40](../../../education/documentation/004_oepfp/math/04_conservative_context_extension_and_descent.md#L40) [education/documentation/004_oepfp/math/07_mathematical_obligations_register.yaml:103](../../../education/documentation/004_oepfp/math/07_mathematical_obligations_register.yaml#L103)

- Cochain specialization declares C0→C1→C2 with d1d0=0; raw quotient Q1=C1/im d0 differs from closed H1. Φ1 is a declared weighted quotient L1 distance, Γ2 closure mass, and dual claims require feasibility. L1 minimizers need not be unique/sparse/integral; deterministic maximal-sparsity then lexicographic face selection is an additional finite optimization policy. [education/documentation/004_oepfp/math/04_math_minimal_representatives_and_hodge.md:46](../../../education/documentation/004_oepfp/math/04_math_minimal_representatives_and_hodge.md#L46) [education/documentation/004_oepfp/math/04_math_minimal_representatives_and_hodge.md:85](../../../education/documentation/004_oepfp/math/04_math_minimal_representatives_and_hodge.md#L85)

- Positive inner products give C1=im d0⊕H1⊕im d1*. A harmonic representative lies in the same repair coset only for closed input. A view constraint d1c=0 is not view-output gauge invariance and does not eliminate database refresh. [education/documentation/004_oepfp/math/04_math_minimal_representatives_and_hodge.md:21](../../../education/documentation/004_oepfp/math/04_math_minimal_representatives_and_hodge.md#L21) [education/documentation/004_oepfp/math/bqnf_cochain_views.md:75](../../../education/documentation/004_oepfp/math/bqnf_cochain_views.md#L75)

- Other fully indexed math branches include detector adequacy, filtered diagrams/persistence/survivors, finite transfer traces and formal zeta series, reversal/dagger quarantine, bounded quantifiers, exact finite quantum/stabilizer models, noncommutative holonomy, higher-degree cochains and conditional Bianchi, and immunological negative selection. Their declarations and evidence classes must stay branch-relative. [education/documentation/004_oepfp/math/README.md:77](../../../education/documentation/004_oepfp/math/README.md#L77)

### Transition and normal-form boundary

- DPO/ACSet experiments use one attributed directed-graph schema, registered rules, explicit injective matches, dangling/protected-incidence/fuel checks, immutable output and independent deciding judges. No arbitrary categorical-schema engine or automatic match search is supplied. [education/documentation/004_oepfp/docs/20_acsets_dpo_and_optional_backends.md:7](../../../education/documentation/004_oepfp/docs/20_acsets_dpo_and_optional_backends.md#L7) [education/documentation/004_oepfp/docs/20_acsets_dpo_and_optional_backends.md:13](../../../education/documentation/004_oepfp/docs/20_acsets_dpo_and_optional_backends.md#L13)

- DPO existence/gluing alone does not guarantee confluence. Current source explicitly leaves global confluence and complete critical-pair enumeration open. Polygraph Newmann-style reasoning needs termination and local-confluence premises; supplied finite joined paths establish only those paths. [education/documentation/004_oepfp/docs/20_acsets_dpo_and_optional_backends.md:45](../../../education/documentation/004_oepfp/docs/20_acsets_dpo_and_optional_backends.md#L45) [education/documentation/004_oepfp/math/math_polygraph_rewriting_and_confluence.md:24](../../../education/documentation/004_oepfp/math/math_polygraph_rewriting_and_confluence.md#L24)

### Executable and formal owners

- Current owner paths declared in Track004 README are pfp, typed_capabilities_v1.py, core_symbol_game and core_symbol_game_runtime. Local grammar recognizer/typed grammar code,23Python files and one small CarrierOrigin Lean module are present; notebooks number200 and stored outputs are not audit executions. [education/documentation/004_oepfp/README.md:11](../../../education/documentation/004_oepfp/README.md#L11) [education/documentation/004_oepfp/lean4/CarrierOrigin.lean:76](../../../education/documentation/004_oepfp/lean4/CarrierOrigin.lean#L76)

- SG-L0…SG-L10, generic mathematical_core/dda_core/packet-kernel and benchmark implementation statuses in the obligations register are attributed claims. The register itself records incomplete caller migration, absent generic semantic congruence and open higher-coherence demand. [education/documentation/004_oepfp/math/07_mathematical_obligations_register.yaml:236](../../../education/documentation/004_oepfp/math/07_mathematical_obligations_register.yaml#L236) [education/documentation/004_oepfp/math/07_mathematical_obligations_register.yaml:270](../../../education/documentation/004_oepfp/math/07_mathematical_obligations_register.yaml#L270)

### Forensic findings

- The requested zero-procedural-string pipeline and universal density-fiber/RG normal-form engine are architecture proposals, not established by this curriculum. Current docs retain experimental backends, fixed-schema graph rewriting, strict reply checking and explicit open semantic interfaces. [education/documentation/004_oepfp/docs/20_acsets_dpo_and_optional_backends.md:4](../../../education/documentation/004_oepfp/docs/20_acsets_dpo_and_optional_backends.md#L4) [education/documentation/004_oepfp/math/07_mathematical_obligations_register.yaml:176](../../../education/documentation/004_oepfp/math/07_mathematical_obligations_register.yaml#L176)

- Source README already reports actual pilot-location/count drift and coda-atlas pilot flaws. It states204Adversary pilotfolders and75matrixentries at an attributed historical commit, and onlytwo coda-atlas prompt pilots; these counts must be reconciled by the dedicated pilot audit. [education/documentation/004_oepfp/README.md:61](../../../education/documentation/004_oepfp/README.md#L61) [education/documentation/004_oepfp/README.md:111](../../../education/documentation/004_oepfp/README.md#L111)

Normal-form artifact paths and complete field excerpts are in `tracks[].normal_form_contract_inventory`; all lesson pages appear in `level_pages`, including their exact source headings.

## 005_oegenong

### Definitions and identities

- Track005 exists as Genesis Ongoing, pinned to H3V7N5QF@5d9488324ce976817987bd83a28d901371cfc073. It reads25manuscripts and H1–H3 climbing rounds; this missing prompt-list entry must still be included in the13-track census. [education/documentation/005_oegenong/README.md:13](../../../education/documentation/005_oegenong/README.md#L13) [education/documentation/005_oegenong/README.md:29](../../../education/documentation/005_oegenong/README.md#L29)

- Indexed constructions include assertions arb, explicit no-xrx constraints, add/copy/remove/identify changes, counted assertion multiplicity, mass and destroyed-given cost accounting, stage embeddings, reachability, swapping two relations, writing collisions without identification, separate leftovers/admission, unbounded feedback and H1cancellation/H2raising/H3twin-fill/cone conditions. [education/documentation/005_oegenong/genesis_ongoing.md:34](../../../education/documentation/005_oegenong/genesis_ongoing.md#L34) [education/documentation/005_oegenong/genesis_ongoing.md:119](../../../education/documentation/005_oegenong/genesis_ongoing.md#L119)

- The D8 result concerns a closed fewest-change count plus explicit reachability witnesses and matching lower bounds. The education filename primal-dual does not make it an LP strong-duality theorem. [education/documentation/005_oegenong/levels/level_08_discrete_primal_dual.md:33](../../../education/documentation/005_oegenong/levels/level_08_discrete_primal_dual.md#L33) [education/documentation/005_oegenong/levels/level_08_discrete_primal_dual.md:37](../../../education/documentation/005_oegenong/levels/level_08_discrete_primal_dual.md#L37)

- The positioned-confluence filename describes a source study of distinct terms colliding in a writing without identification. It is not evidence of global rewrite confluence. [education/documentation/005_oegenong/levels/level_11_positioned_confluence.md:37](../../../education/documentation/005_oegenong/levels/level_11_positioned_confluence.md#L37)

### Transition and normal-form boundary

- Six nf.* copies are educational contracts, not in the pinned H3tree: RPNF,AONF,evidence provenance,DDANF,freshness and CNF. Their presence cannot strengthen pinned code/theorem results. [education/documentation/005_oegenong/normal_forms/README.md:19](../../../education/documentation/005_oegenong/normal_forms/README.md#L19)

### Executable and formal owners

- The one local Python checker recomputes Git blob identities against the pin; three notebooks call the separate pinned package code/xry. Computational ownership therefore includes that paper package and its actual formal modules, not just this education wrapper. [education/documentation/005_oegenong/README.md:32](../../../education/documentation/005_oegenong/README.md#L32) [education/documentation/005_oegenong/curriculum/README.md:16](../../../education/documentation/005_oegenong/curriculum/README.md#L16)

### Forensic findings

- Metadata claim_status:verified does not certify an absent live execution. Read manuscript-specific carriers and the exact H3source declarations; do not rename bounded reachability/collision statements as generic primal-dual, categorical-confluence or autonomous-admission laws. [education/documentation/005_oegenong/README.md:11](../../../education/documentation/005_oegenong/README.md#L11) [education/documentation/005_oegenong/levels/level_11_positioned_confluence.md:37](../../../education/documentation/005_oegenong/levels/level_11_positioned_confluence.md#L37)

Normal-form artifact paths and complete field excerpts are in `tracks[].normal_form_contract_inventory`; all lesson pages appear in `level_pages`, including their exact source headings.

## 006_oewdp

### Definitions and identities

- Edition2.4.1 separates written theorems, mechanized Lean statements and executed finite implementations. The admitted cut is a declared package (X,E,τ,K), with witness roles, irreflexivity, orientation, observer and authority assumptions explicitly added rather than derived from an empty glyph. [education/documentation/006_oewdp/README.md:44](../../../education/documentation/006_oewdp/README.md#L44) [education/documentation/006_oewdp/README.md:78](../../../education/documentation/006_oewdp/README.md#L78)

- For a graph host C0=A^V,C1=A^E,d0f(u,v)=f(v)−f(u), Q1=C1/im d0 is raw repair quotient. With declared d1 and d1d0=0, κ([h])=d1h yields0→H1→Q1→im d1→0. Φ1,Γ2 and closure ratio classify exact, closed-residual and active-closure states only with certified carrier/norm/window data. [education/documentation/006_oewdp/levels/level_03_discrete_complex_cochains.md:70](../../../education/documentation/006_oewdp/levels/level_03_discrete_complex_cochains.md#L70) [education/documentation/006_oewdp/levels/level_03_discrete_complex_cochains.md:146](../../../education/documentation/006_oewdp/levels/level_03_discrete_complex_cochains.md#L146) [education/documentation/006_oewdp/levels/level_03_discrete_complex_cochains.md:57](../../../education/documentation/006_oewdp/levels/level_03_discrete_complex_cochains.md#L57)

- Other indexed topics include symmetry/nonselection, recurrence and constitutive order, path-independent valuations/clocks, additive weights and finite probability, layered observers, descent/gluing, calibration/traceability, five-valued relative-completeness statuses, chain contraction/truncation leakage, semiring path sums and cancellation, finite observation/support/cost bounds, and countermodels to unpaid quantum reconstruction. [education/documentation/006_oewdp/README.md:74](../../../education/documentation/006_oewdp/README.md#L74) [education/documentation/006_oewdp/README.md:40](../../../education/documentation/006_oewdp/README.md#L40)

- Quantum state space, tensor composition, CP instruments and Tsirelson S²≤8 require positive finite Hilbert densities, local observables and trace pairing as additional declared inputs. Algebraic tensor nonfactorability or finite stochastic models alone do not establish physical entanglement or a universal quantum epistemic geometry. [education/documentation/006_oewdp/levels/level_18_exact_rational_bounds.md:122](../../../education/documentation/006_oewdp/levels/level_18_exact_rational_bounds.md#L122) [education/documentation/006_oewdp/levels/level_17_semiring_coarse_graining.md:224](../../../education/documentation/006_oewdp/levels/level_17_semiring_coarse_graining.md#L224)

### Transition and normal-form boundary

- CODA, Prime and DDC routes distinguish candidate proposal, declaration, fill execution, intake/transport checking, continuation/halting and reentry. The cochain DDC alphabet E,R,C,I,Λ,D,M,T is a declared typed operational choice, not an automatic operad proof. [education/documentation/006_oewdp/README.md:48](../../../education/documentation/006_oewdp/README.md#L48) [education/documentation/006_oewdp/levels/prime/level_00_prime_triad_architecture.md:3](../../../education/documentation/006_oewdp/levels/prime/level_00_prime_triad_architecture.md#L3)

- Twenty-eight YAML artifacts in normal_forms-named directories include one schema and two domain copies: twenty-seven contract files in total (root plus CODA copies). All are indexed by exact path/hash/fields. The root README still says twelve while listing more; executable/absent are declared statuses, not a fresh code-verifier binding audit. [education/documentation/006_oewdp/normal_forms/README.md:22](../../../education/documentation/006_oewdp/normal_forms/README.md#L22) [education/documentation/006_oewdp/normal_forms/README.md:27](../../../education/documentation/006_oewdp/normal_forms/README.md#L27)

### Executable and formal owners

- Inspected native responsibility map binds WDP source/protocol presentation to core_solvers finite_computation, core_replay, core_holonomy signed_transport, core_quantum_physics signed_sampling, core_homology simplicial, core_category_theory finite_report_descent and core_general_relativity regge_calculus. core_wdp genesis_extension is the declared CLI; owner-file presence is recorded, not runtime execution. [education/documentation/006_oewdp/levels/level_23_sovereign_difference_grounding.md:51](../../../education/documentation/006_oewdp/levels/level_23_sovereign_difference_grounding.md#L51) [education/documentation/006_oewdp/levels/level_23_sovereign_difference_grounding.md:64](../../../education/documentation/006_oewdp/levels/level_23_sovereign_difference_grounding.md#L64)

- Observation-budget executables are core_wdp distinct_image_completion, observation_cost, calibrated_reports and joint_support_recovery. Their source declarations/hashes and referenced historical tests are inventoried separately; none was run for this audit. [education/documentation/006_oewdp/curriculum/710_wdp_finite_obstruction/concepts/lesson_710_05_observation_budgets_and_cost.md:68](../../../education/documentation/006_oewdp/curriculum/710_wdp_finite_obstruction/concepts/lesson_710_05_observation_budgets_and_cost.md#L68) [education/documentation/006_oewdp/curriculum/710_wdp_finite_obstruction/concepts/lesson_710_05_observation_budgets_and_cost.md:165](../../../education/documentation/006_oewdp/curriculum/710_wdp_finite_obstruction/concepts/lesson_710_05_observation_budgets_and_cost.md#L165)

### Forensic findings

- Track006 retains a second S(n)-named toy family. Its README calls these canonical/formal realizations, but source AdjunctionCochain checks only G(F(x))=x and Polygraph2 is one string replacement. These files differ in bytes from corrected Track002 counterparts and must not be treated as a shared verified implementation. [education/documentation/006_oewdp/code/README.md:7](../../../education/documentation/006_oewdp/code/README.md#L7) [education/documentation/006_oewdp/code/sn_realizations.py:83](../../../education/documentation/006_oewdp/code/sn_realizations.py#L83) [education/documentation/006_oewdp/code/sn_realizations.py:73](../../../education/documentation/006_oewdp/code/sn_realizations.py#L73)

Normal-form artifact paths and complete field excerpts are in `tracks[].normal_form_contract_inventory`; all lesson pages appear in `level_pages`, including their exact source headings.

## Architectural consequences for v1.1RC

1. Treat bare inscriptions, chosen mathematical carriers and runtime packet schemas as separate layers. No source licenses deriving a canonical carrier, arity, Hilbert space or unique operad from `<>`. Supply, admission, interpretation, verification and authority stay distinct.

2. Retain protected questions and exact source-to-owner maps. A retract, equivalence flag, familiar category name or matching dimension is insufficient to transport semantic answers, future transitions, permissions or physical conclusions.

3. Use typed repair/exhaustion/extension outcomes with complete coverage and retained tied minima. Search failure and bounded budget stops stay Unknown; a well-typed rewrite or DPO square does not by itself prove progress, confluence or termination.

4. Present operadic replacement, generic ACSets, epistemic bundles and Wilsonian/Lindblad cognitive dynamics as proposals with explicit model data and additional obligations. A density off-diagonal is basis-dependent and is not automatically entanglement or mutual information; sheaf H1 needs a chosen site/restriction sheaf and hypotheses; coarse-graining fixed points need a specified map and do not automatically equal BQNF. These are mathematical obligations, not findings established by the indexed educational examples.

5. Build on the scoped owners already present. Grammar membership, finite source execution, exact cochain/dual witness checks, observation costs, supplied quantum instruments and finite graph rewrite judges have different evidence types and must not be collapsed into a universal PASS or terminal-object claim.

6. Resolve source availability and stale duplicate documentation before publication. Track000 lacks four advertised primary record files; Track006 retains stronger S(n) toy labels than corrected Track002; Track006 normal-form counts disagree with its directory; numerous renamed-path references remain unresolved. Preserve all as explicit audit items rather than silently treating navigation/metadata as mathematical evidence.

## Reproducibility and limits

The inventory was generated by `/workspace/scratch/oepfp-audit/inventory_curriculum_000_006.py` and supplemented by `/workspace/scratch/oepfp-audit/synthesize_curriculum_000_006.py`. These tools read repository bytes and write only scratch artifacts. No source or governance file was edited. File hashes describe the working-tree bytes observed at the recorded HEAD, not a claim that every file equals its Git blob. The JSON distinguishes tracked paths and unexecuted source/receipt classes.
