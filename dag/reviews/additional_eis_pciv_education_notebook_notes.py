"""Record full JSON/scaffold readings separately from cell execution."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REV = ROOT / 'dag/reviews'
scope = json.loads((REV / 'additional_eis_pciv_education_remaining_scope.json').read_text())
notes_by_stem = {
 'lesson_500_01_eis_architecture_overview': 'Complete notebook JSON and four code cells read. The class initializes a clean/non-admitted report but leaves is_admitted mutable. Its falsifier manually raises PermissionError rather than attempting the forbidden assignment; a fresh direct assignment succeeds. Prediction is a self-comparison of one literal. This does not verify a real admission boundary.',
 'lesson_510_01_anti_skills_and_mutation_gaps': 'Complete notebook read. The miniature Antibody constructor genuinely refuses a non-candidate status, a useful positive teaching check, but public attributes remain mutable. The exception-only negative cell would silently complete if the guard were removed; prediction merely compares its own constant. No candidate farm, mining, registry or two-signal runtime is exercised.',
 'lesson_520_00_innate_pharmacy_barriers': 'Complete notebook read. It checks the length of a literal twelve-name list and that a handcrafted dictionary lacks a repair key. This is vocabulary/schema illustration, not execution of twelve detectors or a Finding validator. Prediction is a literal self-comparison and no Rust/native code runs.',
 'lesson_520_01_component_role_partitioning': 'Complete notebook read. Its class genuinely checks PROPOSED and runtime_enforcement=False, improving on the concept-page dataclass. However its negative test has no assertion if construction unexpectedly succeeds. Removing both guards in an in-memory mutant lets all four cells finish and creates invalid_spec; the constant prediction still passes.',
 'lesson_520_02_fixture_polarity_and_near_misses': 'Complete notebook read. The primary check only counts two supplied tuples; no detector runs. The falsifier sets detector_hits_near_miss=True and asserts that same value before claiming mismatch detection. Prediction is also a constant self-comparison. These are illustrative fixtures, not measured polarity enforcement.',
 'lesson_520_03_central_tolerance_and_thymus_gate': 'Complete notebook read. A substring against two fixed self strings genuinely demonstrates a bounded negative filter. The separate clearance check compares two unequal status strings and supplies no admission mechanism. This supports only the tiny provided panel/example, not current canonical-panel custody or general tolerance.',
 'lesson_520_04_learned_guard_two_signal_activation': 'Complete notebook read. Three fixed Booleans demonstrate the activation conjunction. A locally raised exception on a preset missing-signal value does not test causal independence or the real gate. There is no provenance field or copied-signal rejection. Prediction is an unrelated literal self-comparison.',
 'lesson_520_05_independent_observation_support_policy': 'Complete notebook read. The set calculation correctly counts three key strings and removes one duplicate. It establishes no independence model; the negative cell only asserts2<3 without invoking a promotion gate. The confirmed prediction is a constant, not a measured outcome.',
 'lesson_520_06_provisional_custody_and_review_queue': 'Complete notebook read. A membership test and a local conditional exception illustrate the FINDING-only policy. There is no registry, review queue, external admission or state-writing operation. The broad custody verification language should be scoped to these declared toy values.',
 'lesson_520_07_clonal_selection_and_affinity': 'Complete notebook read. Fraction42/50=21/25 is exact; a separate local float-type check illustrates a refusal branch. Neither versioned mutation nor a production metric boundary is exercised. The source does not infer accuracy from affinity and should retain that limited arithmetic scope.',
 'lesson_520_08_regulatory_supervision_and_anergy': 'Complete notebook read. A plain two-field object and comparison0.15>0.10 precede a claim that a proposal was emitted to an epoch queue, but no queue operation exists. Self-suspension is simulated by an unconditional raise. Prediction is a constant, not queue evidence or regulatory enforcement.',
 'lesson_520_09_external_admission_boundary': 'Complete notebook read. It checks a self-computed digest and that different literal rule bytes have a different digest. The literal SIG_HUMAN_01 string is never verified and operational scope is absent. This is local byte-consistency evidence, not authenticated external human admission.',
 'lesson_520_10_antimorphism_polarity_and_bounded_telemetry': 'Complete notebook read. Literal barcodes/status fields are asserted; no homology algorithm or enforcement boundary exists. The falsifier prints a rejection claim on the unchanged None authority branch, which never raises. It cannot establish a real telemetry hold or antimorphism law.',
 'lesson_400_00_substrate_and_packaging': 'Complete notebook JSON/metadata and sole code cell read. It hashes a four-field JSON object twice with matching inputs; useful determinism example, but it creates no ExecutionOccurrence and admits floats/nonfinite values through ordinary json.dumps. It does not validate the restricted production genome codec. Fresh reviewed cell execution passed its one positive assertion.',
 'lesson_400_01_lineage_dag_and_causal_descent': 'Complete two-cell notebook read. Separate dictionaries preserve the shown reference-edge distinction, but insertion lacks cycle/self-loop checking. A fresh two-edge mutation cycle is accepted; this is a miniature teaching-class finding, not a claim about the production genealogy implementation.',
 'lesson_400_02_mutation_operators_and_forge': 'Complete notebook read. The supplied overlapping replacement is refused, while zero-width insertion at position1 inside protected(0,3) changes ABC to A!BC. It uses string slicing despite naming prompt_bytes and has no span-admission checks. The negative-test branch merely prints an error on failure. Fresh isolated cells and the insertion control ran.',
 'lesson_400_03_lamarckian_retro_inheritance': 'Complete notebook read. Four values of a scalar floating-point attenuation function pass; these dyadic values happen to be exact. There is no ancestry graph, witness receipt, original-age binding or no-reset test, and negative/nonintegral hops are not admitted explicitly. Useful limited arithmetic illustration only.',
 'lesson_410_04_pareto_selection_and_fitness': 'Complete notebook read. The positive two-coordinate rational comparison passes. Unchecked zip truncates unequal vectors, and floats are also accepted; fresh controls confirm both. It neither computes an entire Pareto frontier nor handles the four-coordinate orientation issue in the larger specification.',
 'lesson_410_05_inverse_lineage_pagerank': 'Complete notebook read. It computes85/100times the sum of two child scores, correctly obtaining255/400. No transition matrix, dangling-node policy, stationary equation, normalization or fixed-point certificate is implemented. Reuse as one local weighted-credit arithmetic example, not a PageRank solver.',
 'lesson_410_06_precedent_retrieval_and_evaporation': 'Complete notebook read. Floating exponential half-life examples at5and10epochs pass. There is no matching/retrieval implementation, original-age custody or rational wire contract. Negative elapsed time and nonpositive half-life are not validated; these boundaries remain outside the demonstrated examples.',
 'lesson_420_07_ecological_reserves_and_population': 'Complete notebook read. The capacity20 positive control passes, but converting exact quotas to float loses fractional priorities. At10^20+1 the last seat goes to baseline rather than frontier under the same tie policy; the exact Fraction comparison reproduces the mismatch. Restricted small-capacity behavior is not a proof of exact arbitrary-integer allocation.',
 'lesson_420_08_lineage_taint_and_custody_invalidation': 'Complete notebook read. The visited-set traversal computes forward graph reachability and avoids collateral branches in its sample. Independent closure agrees for all512three-vertex digraphs and allthree roots(1536checks), including cycles. This is useful finite algorithm evidence, not authentication that input edges represent real causal inheritance.',
 'lesson_420_09_durable_event_log_and_persistence': 'Complete notebook read. It reserializes a payload and compares a supplied digest with an assert. It does not implement an event log, idempotency, event IDs, crash recovery or provider suppression; the markdown overstates what this local hash-consistency example verifies. Stored outputs are empty; fresh cell execution passed.',
 'lesson_420_10_open_horizons_and_multi_island_ecology': 'Complete notebook read. The toy list transfer works for valid indices but removes the source genome before validating the destination. An invalid destination raises IndexError after the genome is lost. No homologous crossover, quota, compatibility policy or transactional persistence is implemented; no production ecology was exercised.',
}
notes = {}
for row in scope['files']:
    path = row['path']
    selected_notebook = path.startswith(('education/010_oepciv/curriculum/', 'education/009_oeeis/curriculum/')) and path.endswith('.ipynb')
    scaffold = path.endswith(('.gitkeep', '/lakefile.lean', '/lean-toolchain'))
    if not (selected_notebook or scaffold):
        continue
    data = (ROOT / path).read_bytes()
    assert hashlib.sha256(data).hexdigest() == row['sha256']
    if selected_notebook:
        note = notes_by_stem[Path(path).stem]
        book = json.loads(data)
        assert all(c.get('execution_count') is None and not c.get('outputs') for c in book['cells'] if c['cell_type'] == 'code')
        note += ' Original execution counts are null and output arrays empty; originals were not rewritten.'
    elif path.endswith('.gitkeep'):
        note = 'Complete placeholder comment read in its curriculum directory. It preserves the scripts/video folder and contains no lesson, execution result or mathematical claim.'
    elif path.endswith('/lakefile.lean'):
        note = 'Complete Lake package/library declaration read. It names the intended educational library root and version; build configuration is not a checked theorem. No Lean build was run.'
    else:
        note = 'Complete pinned Lean toolchain line read: leanprover/lean4:v4.35.0. A toolchain declaration is reproducibility metadata, not proof compilation evidence; no installation/build performed.'
    notes[path] = note
assert len(notes) == 36
(REV / 'additional_eis_pciv_education_notebook_notes.json').write_text(json.dumps(notes, indent=2) + '\n')
print(json.dumps({'full_body_notes': len(notes), 'notebook_bodies': len(notes_by_stem)}))
