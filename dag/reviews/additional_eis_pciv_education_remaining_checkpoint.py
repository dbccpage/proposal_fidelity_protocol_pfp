"""Persist teaching-source readings and keep the unfinished slice explicit."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REV = ROOT / 'dag/reviews'
scope = json.loads((REV / 'additional_eis_pciv_education_remaining_scope.json').read_text())
frozen = {r['path']: r for r in scope['files']}
target = REV / 'additional_eis_pciv_education_remaining.json'
prior = json.loads(target.read_text()) if target.exists() else {'file_reviews': []}
rows = {r['path']: r for r in prior['file_reviews']}
eis = 'education/009_oeeis/'
pciv = 'education/010_oepciv/'
notes = {
 eis+'oeeis_notes.md': 'Full regeneration ticket read. It explicitly distinguishes1000trailed entries from40base contents, preserves the old panel/seal and asks for400new verified bases. This is a useful evidence-quality correction and a proposed regeneration, not evidence it happened. Actual current panel/loader findings belong to the separate PFP domain review.',
 eis+'oeeis_anti_skills_and_mutation_gaps.md': 'Full mutation-gap/anti-skill register read. Useful requirements distinguish prefix legality, local versus global conditioning, exact wire policy, typed refusal, task-preserving repair, finite evidence and implementation plans. Historical registry counts and MUB observations are explicitly tied to201dc8d and external review; this reading does not replay them or establish that the candidate detector was admitted. Anti-skills are predicates/policies, not antimorphisms or a proof of universal detection.',
 eis+'normal_forms/README.md': 'Full index and level mapping read. It presents production/computed/gated status and misidentifies the linked CDC, ODNF and EFNF contracts; the YAML instead describes row-change evidence, observer distinguishability and permission-bound temporal projection. Four linked contracts say verification absent. Useful intended mapping needs correction before it can ground an implemented EIS claim.',
 eis+'normal_forms/nf.epistemic.enf.yaml': 'Complete draft claim-envelope contract read. Requiring who/when/uncertainty/challenge fields is useful provenance structure, but evidence and subordinate-verifier adequacy remain premises. No normalizer, confluence/uniqueness proof or omniscience guarantee is provided. The local schema requires a loss-ledger trigger field that is absent.',
 eis+'normal_forms/nf.epistemic.odnf.yaml': 'Complete observer-distinguishability proposal read. It asks for contexts, equivalence relations and transport witnesses and correctly disclaims universal classical gluing/physical representation. Cochain symbols have no concrete groups/maps here; the complex and d1d0=0 would need admission. It does not specify statistically independent witnesses or an observation quorum. Verification is absent and one required schema field is missing.',
 eis+'normal_forms/nf.evidence.cdc.yaml': 'Complete change-event evidence contract read. Old/new rows, changed attributes, group keys and predicate transitions can support incremental database reasoning. This is not the index\'s causal derivation certificate or a proof preventing hallucination. It declares no physical ordering guarantee and no certificate; required loss-ledger trigger field is missing.',
 eis+'normal_forms/nf.evidence.loss_ledger.yaml': 'Complete loss-accounting proposal read. It preserves declared erasures/precision losses and explicitly says logging does not prevent loss. Completeness of the reported erasures is an external checking obligation, not a consequence of nonempty entries. One local schema-required field is absent.',
 eis+'normal_forms/nf.security.efnf.yaml': 'Complete temporal projection/fibration contract read. The typed commutation square is a meaningful consistency condition under independently sound permission projections, and the text correctly rejects identity-projection-as-authorization. It leaves permission soundness open and does not supply a concrete verifier here. It is not the firewall/token-limits contract described in the index.',
 eis+'normal_forms/normal_form_contract_schema.yaml': 'Complete custom meta-schema read. It distinguishes theory/contract/verification status and requires exact local-to-canonical route maps and a loss-ledger trigger field. This is a schema specification, not a JSON Schema validator or a semantic proof engine. Selected declared structural predicates were independently checked for all ten local contracts.',
 pciv+'normal_forms/README.md': 'Complete PCIV normal-form index read. Lineage, Pareto and protected-lift ideas are useful design mappings but need actual adapters. The linked provenance contract is about semiring-annotated query tuples, not cryptographic causal ancestry/taint; scalar separation cost is not by itself a four-objective Pareto algorithm. Its production/computed/gated metadata exceeds the absent provenance-verification status.',
 pciv+'normal_forms/nf.derivation.pdnf.yaml': 'Complete witnessed-irreflexive-relation contract read. Given an asserted positive witness and irreflexivity, related elements are distinct and require at least two carrier members. Irreflexivity is explicitly admitted, not derived from an inscription or bare positive relation. Upstream finite classifications/open obligations are correctly scoped; no upstream Lean build was rerun and no PCIV-specific mutation adapter follows merely from the label.',
 pciv+'normal_forms/nf.derivation.rpnf.yaml': 'Complete replay contract read. Recomputing a declared deterministic fold from a declared genesis can establish equality to a target regime; presentation/admission and duplicate policy are explicit. This cannot prove actual historical occurrence, next-event choice or that arbitrary runtime events implement that fold. Upstream theorem references remain inherited references, not newly checked proofs.',
 pciv+'normal_forms/nf.derivation.scnf.yaml': 'Complete measure-relative minimum contract read. Keeping the declared cost, isomorphism relation and all tied minimizers is useful mathematical discipline. Completeness/minimality depends on the admitted candidate domain or a valid certificate; a list of values is not sufficient by itself. This scalar separation formulation does not instantiate PCIV multi-objective Pareto selection without an adapter.',
 pciv+'normal_forms/nf.derivation.sernf.yaml': 'Complete split-retraction contract read. The identity r(u(x))=x gives a set-theoretic section/retraction on its declared carrier and does not imply reverse isomorphism. Checking only generators requires additional homomorphism assumptions; full set retraction alone does not preserve arbitrary algebraic relations. Two exact Z/4Z countercontrols expose these omitted premises. One schema-required field is absent.',
 pciv+'normal_forms/nf.evidence.provenance.yaml': 'Complete semiring query-provenance proposal read. Annotated tuple derivations are a useful declared algebraic structure, with explicit privacy/security limitations. They do not establish a cryptographic event chain, authenticated causal ancestry or descendant quarantine. Verification status is absent and a required schema field is missing.',
 pciv+'normal_forms/normal_form_contract_schema.yaml': 'Exact byte-for-byte transfer from the fully read EIS sibling meta-schema, SHA256 b7f991076733d9de27c6b5b772079929c0ed7566800a89f01740126cfcefa20a. All6691bytes match, so the same source-body assessment applies; this is not a new independent implementation.',
 pciv+'normal_forms/nf_01_prompt_society_and_civilization.md': 'Complete society/civilization specification and embedded schema read. It proposes coordination, independent evaluation, dominance, quota and reservation laws. Four objective coordinates in the prose become only three in the schema; raw cost direction is not normalized despite an all-maximize comparison. A schema-valid fixture violates the prose migration quota. Shape validation cannot alone prove optimal routing, concurrent budget conservation or causal/cryptographic authenticity.',
 pciv+'normal_forms/nf_02_lamarckian_pfp_adversary_loop.md': 'Complete state-machine, protected-core and attenuation specification read. Failure-conditioned mutation and w=2^-d are useful hypotheses, and the text correctly disclaims guaranteed fitness improvement. Its schema accepts arbitrary residual strings and weight1 at hop3 instead of1/8; semantic witnesses/core comparisons need separate enforcement. Header verified status does not supply the proposed end-to-end test.',
 pciv+'normal_forms/nf_03_run_u_cemetery_and_antibody_gate.md': 'Complete cemetery-gate proposal and schema read. Exact/pattern reuse can block repeated admitted failures but cannot catch all semantic refactorings or prove convergence; the text explicitly states those limits. The ablation flag bypasses both cemetery and antibody predicates in the displayed policy. Schema descriptions do not enforce the headstone: ID prefix or nonempty witness. No runtime gate was invoked or claimed bypassed.',
}
curriculum_notes = REV / 'additional_eis_pciv_education_curriculum_notes.json'
if curriculum_notes.exists():
    notes.update(json.loads(curriculum_notes.read_text()))
notebook_notes = REV / 'additional_eis_pciv_education_notebook_notes.json'
if notebook_notes.exists():
    notes.update(json.loads(notebook_notes.read_text()))
level_notes = REV / 'additional_eis_pciv_education_level_notes.json'
if level_notes.exists():
    notes.update(json.loads(level_notes.read_text()))
for path, note in notes.items():
    raw = (ROOT / path).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == frozen[path]['sha256']
    rows[path] = {'path': path, 'sha256': frozen[path]['sha256'], 'full_source_read': True,
                  'reviewed_lines': [[1, len(raw.decode('utf-8').splitlines())]], 'assessment': note}


def ev(path):
    return {'path': path, 'sha256': frozen[path]['sha256']}


findings = [
 {'id': 'EPE-F001', 'severity': 'medium', 'statement': 'The normal-form indexes misbind several claimed mechanisms to their linked contracts: CDC is row-change evidence, ODNF observer distinguishability, EFNF temporal permission projection, and provenance is semiring query annotation. These are not the claimed causal-derivation, independent-observation, firewall/token-limit or cryptographic lineage contracts. Production/computed/gated metadata also coexists with five verification-absent YAML entries.',
  'evidence': [ev(eis+'normal_forms/README.md'), ev(pciv+'normal_forms/README.md'), ev(eis+'normal_forms/nf.evidence.cdc.yaml'), ev(eis+'normal_forms/nf.epistemic.odnf.yaml'), ev(eis+'normal_forms/nf.security.efnf.yaml'), ev(pciv+'normal_forms/nf.evidence.provenance.yaml')],
  'recommended_action': 'Correct the names and scope of each linked contract; separately define and validate the domain adapters and qualify evidence metadata.'},
 {'id': 'EPE-F002', 'severity': 'medium', 'statement': 'Six of the ten local YAML contracts omit certification.loss_ledger_trigger_id, which their adjacent custom meta-schema requires. Both exact schema copies agree. Terminal-route domains and canonical targets do match for all ten.',
  'evidence': [ev(eis+'normal_forms/normal_form_contract_schema.yaml'), ev(pciv+'normal_forms/normal_form_contract_schema.yaml')],
  'validation': 'dag/reviews/additional_eis_pciv_education_normal_form_checks.json',
  'recommended_action': 'Add the appropriate declared trigger or null after reviewing the intended policy, and bind metadata to an actual schema-validation result.'},
 {'id': 'EPE-F003', 'severity': 'medium', 'statement': 'SERNF says checking finite generators decides the split identity and that a section preserves base relations, without declaring homomorphism/structure-preservation premises. On additive Z/4Z, u=id and r=(0,1,3,3) pass0/1 but fail at2. Conversely u(x)=x+1 and r(y)=y-1 satisfy the round trip everywhere while u fails to preserve addition.',
  'evidence': [ev(pciv+'normal_forms/nf.derivation.sernf.yaml')],
  'validation': 'dag/reviews/additional_eis_pciv_education_normal_form_checks.json',
  'recommended_action': 'Check every member of a declared finite carrier, or supply an algebraic presentation and prove the maps are appropriate homomorphisms. State relation preservation separately from a set-theoretic retraction.'},
 {'id': 'EPE-F004', 'severity': 'medium', 'statement': 'The three normative PCIV JSON schemas do not enforce the associated semantic laws. Schema-valid controls allow a100-entry migration quota for one family, arbitrary cochain strings and attenuation weight1 at hop3, and a headstone identifier without its described prefix plus an empty witness. This bounds what schema conformance means; it is not a demonstrated runtime exploit.',
  'evidence': [ev(pciv+'normal_forms/nf_01_prompt_society_and_civilization.md'), ev(pciv+'normal_forms/nf_02_lamarckian_pfp_adversary_loop.md'), ev(pciv+'normal_forms/nf_03_run_u_cemetery_and_antibody_gate.md')],
  'validation': 'dag/reviews/additional_eis_pciv_education_normal_form_checks.json',
  'recommended_action': 'Separate shape and semantic validation, add enforceable field constraints, and require bound witnesses/state checks for cross-field and concurrency invariants.'},
 {'id': 'EPE-F005', 'severity': 'medium', 'statement': 'The society definition uses a four-coordinate rational Pareto frontier while its wire schema names only accuracy,cost,robustness. Its written dominance law maximizes every coordinate without a declared transformation for cost. If cost means raw expenditure, equal other scores and higher cost pass that law; if it means utility, that conversion must be explicit.',
  'evidence': [ev(pciv+'normal_forms/nf_01_prompt_society_and_civilization.md')],
  'recommended_action': 'Declare all coordinates, units and minimize/maximize direction, and align the wire schema with the mathematical comparison. Preserve ties and hold-out evaluation as separate obligations.'},
]
claims = [
 {'id': 'EPE-C01', 'statement': 'These teaching contracts contribute useful typed specifications: claim provenance, explicit loss accounting, admitted observation/transport contexts, independently sound permission projections, witnessed irreflexivity, deterministic replay and measure-relative minima. Their force is conditional on actual carriers, maps and validators, not on a normal-form label.',
  'evidence': [ev(eis+'normal_forms/nf.epistemic.enf.yaml'), ev(eis+'normal_forms/nf.security.efnf.yaml'), ev(pciv+'normal_forms/nf.derivation.pdnf.yaml'), ev(pciv+'normal_forms/nf.derivation.scnf.yaml')]},
 {'id': 'EPE-C02', 'statement': 'The anti-skill register and self-panel regeneration ticket explicitly limit finite evidence, distinguish detection from antimorphisms, preserve failed runs and historical panels, and separate live model results from mock behavior. These are useful review policies and proposed repairs; this source reading does not demonstrate their universal enforcement.',
  'evidence': [ev(eis+'oeeis_anti_skills_and_mutation_gaps.md'), ev(eis+'oeeis_notes.md')]},
]
if curriculum_notes.exists():
    base = eis + 'curriculum/520_eis_levels/concepts/'
    findings.extend([
      {'id': 'EPE-F006', 'severity': 'medium', 'statement': 'Five literal EIS lesson snippets do not enforce adjacent advertised falsifiers. Frozen defaults accept ADMITTED status, the two-signal conjunction accepts a copied true signal, distinct labels on a shared event count as three supports, Fraction converts to float without error, and the signature dataclass accepts empty strings. These are teaching-snippet findings; actual runtime behavior is separately reviewed.',
       'evidence': [ev(base+'lesson_520_01_component_role_partitioning.md'), ev(base+'lesson_520_04_learned_guard_two_signal_activation.md'), ev(base+'lesson_520_05_independent_observation_support_policy.md'), ev(base+'lesson_520_07_clonal_selection_and_affinity.md'), ev(base+'lesson_520_09_external_admission_boundary.md')],
       'validation': 'dag/reviews/additional_eis_pciv_education_lesson_checks.json',
       'recommended_action': 'Label incomplete snippets as illustrative, or replace them with runnable examples that exercise a pinned validating implementation and its negative controls.'},
      {'id': 'EPE-F007', 'severity': 'medium', 'statement': 'The concept pages overextend finite or label-based evidence: passing retained near misses does not ensure valid code never triggers, and distinct correlation keys do not establish pairwise-uncorrelated or causally independent observations. The useful properties are finite-panel agreement and cardinality of an admitted equivalence partition.',
       'evidence': [ev(base+'lesson_520_02_fixture_polarity_and_near_misses.md'), ev(base+'lesson_520_05_independent_observation_support_policy.md')],
       'validation': 'dag/reviews/additional_eis_pciv_education_lesson_checks.json',
       'recommended_action': 'Name the exact fixture population, justify how keys collapse shared causes, and keep statistical independence/error assumptions explicit.'},
      {'id': 'EPE-F008', 'severity': 'low', 'statement': 'Of87local links in31fully read curriculum/concept pages,38do not resolve inside the current checkout. PCIV level links ascend too few directories; several old runtime/planning paths and eleven superseded EIS notebook filenames are also broken. Correct companion notebook links are present separately on the EIS pages.',
       'evidence': [ev(pciv+'curriculum/400_prompt_civ_foundations/concepts/lesson_400_00_substrate_and_packaging.md'), ev(base+'lesson_520_00_innate_pharmacy_barriers.md')],
       'validation': 'dag/reviews/additional_eis_pciv_education_curriculum_links.json',
       'recommended_action': 'Fix internal relative paths and remove superseded duplicate notebook links; mark unavailable foreign runtime references explicitly.'},
    ])
    claims.append({'id': 'EPE-C03', 'statement': 'The concept curriculum identifies reusable policies: prompt material versus execution occurrence, ancestry versus citation, protected-span mutation, finite reachability quarantine, rational comparisons, capacity allocation, candidate-only detector mutation and non-authoritative telemetry. Their names and teaching examples do not supply statistical efficacy, authenticated history or universal enforcement.',
                   'evidence': [ev(pciv+'curriculum/README.md'), ev(eis+'curriculum/500_eis_overview/concepts/lesson_500_01_eis_architecture_overview.md')]})
if notebook_notes.exists():
    foundations = pciv + 'curriculum/400_prompt_civ_foundations/notebooks/'
    ranking = pciv + 'curriculum/410_selection_ranking_retrieval/notebooks/'
    ecology = pciv + 'curriculum/420_population_reserves_persistence/notebooks/'
    findings.extend([
      {'id': 'EPE-F009', 'severity': 'medium', 'statement': 'Several PCIV workbench labels exceed the implemented examples. The PageRank cell is a scalar damped sum without a stationary-equation certificate; the replay cell only checks a supplied payload digest and has no event fold or idempotency; the island cell transfers list entries without crossover or quotas. They are limited teaching examples, not standalone certified workflows.',
       'evidence': [ev(ranking+'lesson_410_05_inverse_lineage_pagerank.ipynb'), ev(ecology+'lesson_420_09_durable_event_log_and_persistence.ipynb'), ev(ecology+'lesson_420_10_open_horizons_and_multi_island_ecology.ipynb')],
       'recommended_action': 'Rename the demonstrations to their actual computed property, or connect them to a pinned implementation and check the stated certificate/state invariant.'},
      {'id': 'EPE-F010', 'severity': 'medium', 'statement': 'Fresh controls on the reviewed PCIV teaching cells expose five guard/algorithm gaps: a two-edge inheritance cycle is admitted; zero-width insertion inside a protected span succeeds; Pareto zip ignores trailing coordinates and accepts floats; float quotas assign the last seat incorrectly at capacity10^20+1; and an invalid island target loses a genome before raising. These findings apply to the miniature notebook implementations, not automatically to production classes.',
       'evidence': [ev(foundations+'lesson_400_01_lineage_dag_and_causal_descent.ipynb'), ev(foundations+'lesson_400_02_mutation_operators_and_forge.ipynb'), ev(ranking+'lesson_410_04_pareto_selection_and_fitness.ipynb'), ev(ecology+'lesson_420_07_ecological_reserves_and_population.ipynb'), ev(ecology+'lesson_420_10_open_horizons_and_multi_island_ecology.ipynb')],
       'validation': 'dag/reviews/additional_eis_pciv_education_pciv_notebook_checks.json',
       'recommended_action': 'Add explicit input/graph/span admission, retain rational remainders, and validate all mutation targets before changing state. Include these controls in the lesson rather than treating a positive printout as a certificate.'},
    ])
    claims.append({'id': 'EPE-C04', 'statement': 'All11fully read PCIV notebook code cells run on their retained standard-library toy examples. The forward-taint function also agrees with independent reachability closure on all512three-vertex directed graphs and allthree roots(1536checks). This is bounded algorithm evidence; the other edge-case findings remain and no causal-ancestry or model-performance claim follows.',
                   'evidence': [ev(ecology+'lesson_420_08_lineage_taint_and_custody_invalidation.ipynb')],
                   'validation': 'dag/reviews/additional_eis_pciv_education_pciv_notebook_checks.json'})
eis_notebook_checks = REV / 'additional_eis_pciv_education_eis_notebook_checks.json'
if eis_notebook_checks.exists():
    labs = eis + 'curriculum/520_eis_levels/notebooks/'
    findings.append({'id': 'EPE-F011', 'severity': 'medium',
        'statement': 'All 13 EIS notebook prediction cells assign a literal and compare it with that same literal, independently of the measured state. Several falsifiers manually raise errors or assert preset flags. The overview report permits direct admission assignment, and removing both role-constructor guards in memory still lets every lesson cell complete because the negative test never fails when its expected exception is absent. Queue emission and human signatures are also only narrated/literal in their examples.',
        'evidence': [ev(eis+'curriculum/500_eis_overview/notebooks/lesson_500_01_eis_architecture_overview.ipynb'), ev(labs+'lesson_520_01_component_role_partitioning.ipynb'), ev(labs+'lesson_520_02_fixture_polarity_and_near_misses.ipynb'), ev(labs+'lesson_520_08_regulatory_supervision_and_anergy.ipynb'), ev(labs+'lesson_520_09_external_admission_boundary.ipynb')],
        'validation': 'dag/reviews/additional_eis_pciv_education_eis_notebook_checks.json',
        'recommended_action': 'Collect a learner prediction before computing the result, compare it with actual output, and exercise a real operation in each negative test with an explicit failure if rejection is absent. Keep toy arithmetic, simulated exceptions and actual runtime evidence distinct.'})
    claims.append({'id': 'EPE-C05', 'statement': 'The 13 fully read EIS notebooks contain 52 reviewed standard-library cells that complete on their fixed toy inputs. Candidate/spec constructors include genuine limited rejection checks, the two-string thymus example computes a real substring match, and the rational-affinity example computes 21/25. This is small teaching-example evidence; constant predictions, simulated falsifiers and absent runtime adapters remain explicit limitations.',
                   'evidence': [ev(eis+'curriculum/510_eis_anti_skills/notebooks/lesson_510_01_anti_skills_and_mutation_gaps.ipynb'), ev(labs+'lesson_520_03_central_tolerance_and_thymus_gate.ipynb'), ev(labs+'lesson_520_07_clonal_selection_and_affinity.ipynb')],
                   'validation': 'dag/reviews/additional_eis_pciv_education_eis_notebook_checks.json'})
if level_notes.exists():
    findings.extend([
      {'id': 'EPE-F012', 'severity': 'medium', 'statement': 'The PCIV teaching notebook and level specify different algorithms: at capacity10 the written Front/Unmeasured/Baseline tie priority gives [6,3,1], while reverse-index ordering gives [6,2,2]; halfway to a half-life, continuous notebook decay is about0.7071 while the level floor-exponent policy is1. The latter is a policy mismatch, not proof that either decay choice is intrinsically incorrect.',
       'evidence': [ev(pciv+'levels/level_06_precedent_retrieval_and_evaporation.md'), ev(pciv+'levels/level_07_ecological_reserves_and_population.md'), ev(pciv+'curriculum/410_selection_ranking_retrieval/notebooks/lesson_410_06_precedent_retrieval_and_evaporation.ipynb'), ev(pciv+'curriculum/420_population_reserves_persistence/notebooks/lesson_420_07_ecological_reserves_and_population.ipynb')],
       'validation': 'dag/reviews/additional_eis_pciv_education_level_checks.json',
       'recommended_action': 'Declare the intended tie priority and decay convention once, and make teaching examples check intermediate boundaries and exact ties against that policy.'},
      {'id': 'EPE-F013', 'severity': 'low', 'statement': 'The identity level says changes always yield distinct finite digests, and the catalog says UUIDv5 plus payload hashes guarantee zero duplicate provider calls. A finite hash is not an injective map on arbitrary messages; collision resistance is a security assumption. At-most-once provider effects also require an actual crash/retry/idempotency protocol beyond content naming.',
       'evidence': [ev(pciv+'levels/level_00_substrate_and_packaging.md'), ev(pciv+'levels/README.md')],
       'recommended_action': 'Qualify hash guarantees and state the transaction/idempotency assumptions. Keep content equality, recorded custody and external side-effect counts separate.'},
    ])
    claims.append({'id': 'EPE-C06', 'statement': 'The levels add meaningful normative obligations absent from several toy cells: explicit inheritance cycle refusal, exact reserve ties, independently aged usage events, rule-version invalidation versus OR reachability, and a clearly proposed multi-island roadmap. These specifications can guide testable workflows; their header grades do not establish runtime enforcement.',
                   'evidence': [ev(pciv+'levels/level_01_lineage_dag_and_causal_descent.md'), ev(pciv+'levels/level_07_ecological_reserves_and_population.md'), ev(pciv+'levels/level_08_lineage_taint_and_custody_invalidation.md'), ev(pciv+'levels/level_10_open_horizons_and_multi_island_ecology.md')]})
report = {'source_commit': scope['source_commit'], 'status': 'in_progress',
          'scope_manifest': 'dag/reviews/additional_eis_pciv_education_remaining_scope.json',
          'file_reviews': sorted(rows.values(), key=lambda r: r['path']),
          'pending_paths': sorted(set(frozen) - set(rows)), 'claims': claims, 'findings': findings,
          'validation': ['dag/reviews/additional_eis_pciv_education_normal_form_checks.json', 'dag/reviews/additional_eis_pciv_education_lesson_checks.json', 'dag/reviews/additional_eis_pciv_education_curriculum_links.json', 'dag/reviews/additional_eis_pciv_education_pciv_notebook_checks.json', 'dag/reviews/additional_eis_pciv_education_eis_notebook_checks.json', 'dag/reviews/additional_eis_pciv_education_level_checks.json'],
          'limits': [f'Only the recorded {len(rows)} files have complete body readings; all remaining paths are explicitly pending.',
                     'No automatic full-body credit for links, upstream proofs or schema scans. The duplicated6691-byte meta-schema has explicit exact-byte reading transfer.',
                     'No original sources edited, runtime/Lean/native suite executed, provider called or private benchmark consulted.']}
target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print(json.dumps({'full_body_reads': len(rows), 'pending': len(report['pending_paths']), 'claims': len(claims), 'findings': len(findings)}))
