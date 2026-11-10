"""Record the31 complete concept/index readings and check their local navigation."""
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
REV = ROOT / 'dag/reviews'
scope = json.loads((REV / 'additional_eis_pciv_education_remaining_scope.json').read_text())
topic_notes = {
 'lesson_400_00_substrate_and_packaging': 'Useful material/occurrence identity distinction: repeated execution need not create a new genome. Hash identity depends on the exact envelope and codec, not semantic equivalence or authenticated execution. Protected spans require actual enforcement; no native seam was rerun.',
 'lesson_400_01_lineage_dag_and_causal_descent': 'Useful separation of mutation ancestry from reference citations. Typed edge separation alone does not establish acyclicity; generation/order or explicit cycle checks are additionally needed. The page\'s guarantee question omits that premise. No implementation bypass asserted.',
 'lesson_400_02_mutation_operators_and_forge': 'Protected-core/plastic-scaffold mutation is a useful task-preservation policy. Byte-range refusal is an implementation obligation and cannot by itself guarantee that changed surrounding text preserves the same interpreted task. Native behavior remains inherited evidence.',
 'lesson_400_03_lamarckian_retro_inheritance': 'Explicit d<=10 and per-edge2^-d attenuation provide bounded propagation weights. They do not prove benefit or bound aggregate influence without a population/branching or normalization policy. Source-witness authenticity and counter nonreset remain independent obligations.',
 'lesson_410_04_pareto_selection_and_fitness': 'Exact rational dominance avoids comparison rounding for admitted values and cleanly separates refusal compliance from accuracy. The listed latency/cost dimensions still need minimizing or declared utility conversion; all-maximize prose is underdefined. Exact arithmetic does not remove statistical measurement uncertainty.',
 'lesson_410_05_inverse_lineage_pagerank': 'Review-allocation ranking is explicitly separated from proof authority, a useful limit. An exact rational fixed-point certificate needs an actual residual/certificate checker; power iteration need not reach exact equality in finitely many steps. This page does not supply its stopping proof or causal-credit model.',
 'lesson_410_06_precedent_retrieval_and_evaporation': 'Deterministic matching and preserved original age are clear replay policies. The2^(-t/H) expression is a continuous decay model and is generally irrational at fractional exponents; an exact rational implementation needs a declared discrete/approximate representation. Decay alone does not prove relevance or diversity.',
 'lesson_420_07_ecological_reserves_and_population': 'The fractions3/5+1/4+3/20 sum1. Largest-remainder allocation can preserve integer capacity with an explicit tie policy, but small capacities can leave a positive-weight bucket empty. Bucket separation is a policy for exploration, not a general biological or no-monoculture theorem.',
 'lesson_420_08_lineage_taint_and_custody_invalidation': 'Finite forward reachability gives a precise quarantine closure once causal edges and initial taint are trusted. The distinction from global rule disarming is useful. Descendant quarantine is conservative policy and does not prove each descendant has inherited the defect.',
 'lesson_420_09_durable_event_log_and_persistence': 'Stable event IDs, separately checked payload hashes, storage deduplication and deterministic replay can support recovery. Zero repeated provider calls additionally needs transaction/idempotency handling across the crash boundary; a UUID or hash alone does not guarantee it. No real recovery/provider run performed.',
 'lesson_420_10_open_horizons_and_multi_island_ecology': 'Clearly identifies the topic as v0.2 planning/open horizons. Migration and crossover are testable search hypotheses, not guarantees of avoiding local optima. Production/verified header metadata should not promote the planning topic to executed evidence.',
 'lesson_500_01_eis_architecture_overview': 'Useful clean-report-does-not-admit boundary and seven-role architecture. Twelve named failure classes and role partitioning do not establish complete detection or absence of autoimmune behavior; those require actual admitted policies and coverage.',
 'lesson_510_01_anti_skills_and_mutation_gaps': 'Useful separation of candidate mining, match telemetry, independent danger and external supervision. Three deduplicated sources are an operational support threshold, not automatically statistically independent causal evidence. Source receipts still require adequacy/custody qualification.',
 'lesson_520_00_innate_pharmacy_barriers': 'Names twelve barriers and emphasizes no authority from an empty finding list. The Python import sketch is not evidence of a Rust binding or enforcement. Listed falsifiers are requirements; linked laboratory availability is checked separately.',
 'lesson_520_01_component_role_partitioning': 'The role/default-status intent is clear, but the literal frozen dataclass allows status=ADMITTED and runtime_enforcement=True. Immutability after construction is not constructor admission validation; isolated exact snippet control confirms the teaching gap.',
 'lesson_520_02_fixture_polarity_and_near_misses': 'Positive and near-miss controls are useful finite detector tests. Nonempty annotations do not enforce nonemptiness, and passing listed near misses does not show valid code never triggers. Digest consistency requires a trusted expected pin.',
 'lesson_520_03_central_tolerance_and_thymus_gate': 'The small loop correctly implements negative filtering over the provided panel and explicitly withholds admission after a miss. Its scope is only those actual panel entries and the supplied matches method; no universal tolerance/adequacy theorem follows.',
 'lesson_520_04_learned_guard_two_signal_activation': 'The conjunction demonstrates a Boolean gate, but accepts signal2 copied from a true signal1; it cannot enforce the adjacent causal-provenance requirement. The actual runtime is a separate source audit. Quiescent false signals and provenance failure also need distinct semantics.',
 'lesson_520_05_independent_observation_support_policy': 'The exact snippet counts distinct labels. Three distinct labels on one shared event still return3, so neither causal independence nor pairwise decorrelation follows. A correlation-key partition needs an independently justified construction and cannot replace an experimental error model.',
 'lesson_520_06_provisional_custody_and_review_queue': 'The literal function refuses HOLD/REFUSE and routes other values to FINDING, a useful disposition restriction. It does not implement registry writes or authorization, and unknown labels are silently collapsed. Treat it as an illustrative slice rather than the complete custody boundary.',
 'lesson_520_07_clonal_selection_and_affinity': 'Fraction(hits,total_probes) supplies exact arithmetic for admitted integer counts, but the displayed type assertion does not prohibit float conversion; the isolated conversion succeeds. Zero denominator and status validation are not handled by this snippet.',
 'lesson_520_08_regulatory_supervision_and_anergy': 'Externalizing a suspension proposal is a sensible separation of evaluation and control. The snippet only constructs a proposal; it supplies no rate threshold, queue, authorization or self-suspension guard. Those falsifiers need a concrete implementation.',
 'lesson_520_09_external_admission_boundary': 'Binding rule bytes, scope and external authorization is a useful intended contract. The frozen string dataclass accepts empty hash/signature and validates neither cryptographic identity nor scope. This is a demonstrated teaching-snippet gap, not a production authorization bypass.',
 'lesson_520_10_antimorphism_polarity_and_bounded_telemetry': 'The RESEARCH_HOLD/no-authority boundary is useful, but two literal barcode lists do not compute persistent homology or enforce a halt. Opposite policy polarity is not automatically an algebraic antimorphism. No geometric or telemetry runtime was executed.',
}
notes = {}
links = []
for row in scope['files']:
    path = row['path']
    if '/curriculum/' not in path or not ('/concepts/' in path and path.endswith('.md') or path.endswith('/README.md')):
        continue
    source = ROOT / path
    text = source.read_text(encoding='utf-8')
    assert hashlib.sha256(source.read_bytes()).hexdigest() == row['sha256']
    if source.stem == 'README':
        note = 'Complete curriculum/track index read. The described lesson progression and concept/notebook/script/video roles are useful navigation and teaching plans, not additional runtime or experimental evidence. Directory existence and link targets are checked separately; linked source bodies are not credited from this index.'
    else:
        note = topic_notes[source.stem]
    notes[path] = note
    for match in re.finditer(r'\[[^\]]*\]\(([^)]+)\)', text):
        href = match.group(1).strip()
        if '://' in href or href.startswith('#'):
            continue
        href = unquote(href.split('#', 1)[0])
        destination = (source.parent / href).resolve()
        inside = destination.is_relative_to(ROOT)
        links.append({'source': path, 'line': text[:match.start()].count('\n') + 1, 'target': href,
                      'inside_repository': inside, 'exists': destination.exists() if inside else False,
                      'resolved': destination.relative_to(ROOT).as_posix() if inside else 'outside_repository_not_read'})
assert len(notes) == 31
(REV / 'additional_eis_pciv_education_curriculum_notes.json').write_text(json.dumps(notes, indent=2) + '\n')
out = {'reviewed_files': len(notes), 'local_links': len(links), 'broken_or_outside': [r for r in links if not r['exists']],
       'links': links, 'limits': 'Read-only existence checks of links in31fully read pages; no remote URLs followed and no linked source body credit.'}
(REV / 'additional_eis_pciv_education_curriculum_links.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps({'full_read_notes': len(notes), 'local_links': len(links), 'broken_or_outside': len(out['broken_or_outside'])}))
