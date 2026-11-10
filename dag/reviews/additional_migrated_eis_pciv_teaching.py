"""Bound the twelve relocated EIS/PCIV teaching sources and test public countercontrols."""
from fractions import Fraction as Q
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
REV = ROOT/'dag/reviews'
migration = json.loads((ROOT/'dag/migrations/demo_support_verification.json').read_text())
locations = [r for r in migration['locations'] if r['source_repo']=='pfp' and
             any(p in r['original_path'] for p in ('/009_oeeis/code/','/010_oepciv/code/'))]
assert len(locations) == 12
notes = {
 'eis_core.py': 'Complete teaching module read. It implements byte/substring filtering, distinct role labels, finite fixture evaluation, symmetric substring self screening, a Boolean danger input, distinct channel counting, clean-count promotion, token overlap, float false-positive ratios and mutable hashed receipt dictionaries. Its external admission filter never consults its stored thymus or an external decision. AntimorphismEmitter computes no antimorphism. The implementations do not establish statistical independence, verified human admission or detector efficacy.',
 'prompt_civilization_core.py': 'Complete teaching module read. Previously inserted parents and increasing generations constrain the admitted graph; ancestor/descendant walks are concrete. It also implements unrestricted string edits, synthetic phenotype improvement, mixed-direction Pareto selection, finite float inverse-lineage ranking, exponential memory decay, front/score pruning, snapshot taint, a local hash chain and unbounded island lists. Prescribed improvement is not measured; all state/custody and type assumptions need explicit adapters before model comparison.'
}
rows = []
for location in locations:
    raw = (ROOT/location['current_path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == location['current_sha256']
    if location['post_move_adaptation']:
        with zipfile.ZipFile(location['original_archive']) as archive:
            original = archive.read(location['archive_member'])
    else:
        original = raw
    assert hashlib.sha256(original).hexdigest() == location['original_sha256']
    relative = location['original_path'].split('/code/',1)[1]
    if relative in notes:
        note = notes[relative]
    elif relative == 'README.md':
        note = 'Full original archive README and current README read. Module/level catalog and test command only; migration updates the test location. Diagnostic/simulation headings do not establish actual deployment or external authority.'
    elif relative == '__init__.py':
        note = 'Full local class export table read. Re-exports the miniature teaching module, with no added semantic validation or production adapter.'
    elif relative == 'tests/__init__.py':
        note = 'Full one-docstring test package marker read. No executable mathematical behavior.'
    elif relative == 'tests/conftest.py':
        note = 'Full test import setup read. Resolves ancestor markers/fallbacks and prepends the local code directory; this is import plumbing, not a verification result.'
    elif 'test_eis_levels' in relative:
        note = 'Complete11-test source read. Checks simple positive and negative byte/phrase fixtures, role-label inequality, supplied danger Boolean, distinct channel count, clean-count promotion, overlap/append mutation, ratio suppression and receipt shape. No independent witness provenance, authenticated admission or antimorphism law is tested. The external boundary test exercises only innate rejection. No fresh suite execution is credited.'
    else:
        assert 'test_prompt_civilization_levels' in relative
        note = 'Complete11-test source read. Covers a four-node admitted DAG, string mutation, synthetic reflection metrics, a small three-objective frontier, relative float rank ordering/normalization, decay, capacity pruning, current descendant taint, hash-data tamper and list migration. The improvement assertion reads metrics hardcoded by the engine; no evaluator/provider is called. It does not test later descendants, tail truncation or island capacity. No fresh suite execution is credited.'
    rows.append({'path':location['original_path'],'sha256':location['original_sha256'],
                 'full_source_read':True,'reviewed_lines':[[1,len(original.decode('utf-8').splitlines())]],
                 'assessment':note,'current_source':location,
                 'reading_basis':'Complete current body; both original README archive members also fully read; remaining ten bodies exactly unchanged.'})


def load_owner(filename, name):
    owner = next(r for r in locations if r['current_path'].endswith('/'+filename))
    spec = importlib.util.spec_from_file_location(name, ROOT/owner['current_path'])
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module, owner


eis, eis_owner = load_owner('eis_core.py','_reviewed_eis_teaching')
pciv, pciv_owner = load_owner('prompt_civilization_core.py','_reviewed_pciv_teaching')
controls = []


class RejectingThymus:
    def test_negative_selection(self, candidate):
        raise AssertionError('this supplied thymus was consulted')


boundary = eis.ExternalAdmissionBoundary(eis.InnateBarrier(), RejectingThymus())
accepted, receipt = boundary.filter_antigen(eis.Antigen(1,'plain text',(),'untrusted'))
assert accepted and receipt['admitted']
oversize, _ = eis.ExternalAdmissionBoundary(eis.InnateBarrier(max_bytes=1),RejectingThymus()).filter_antigen(eis.Antigen(2,'xx',(),'untrusted'))
assert not oversize
controls.append({'id':'admission_label_boundary','plain_untrusted_admitted':accepted,
                 'supplied_thymus_used':False,'oversize_control_refused':True,
                 'limit':'The toy filter returns a label; this does not demonstrate a production authority grant.'})

ab = eis.Antibody(1,'marker',0.8)
guard = eis.TwoSignalGuard(ab)
assert guard.evaluate('marker',True) == 'ACTIVATED_IMMUNE_RESPONSE'
assert guard.evaluate('marker',False) == 'SIGNAL1_ONLY_QUIESCENT'
assert eis.SupportPolicy(0).check_consensus([])
controls.append({'id':'signal_and_support_scope','supplied_true_activates':True,'supplied_false_quiescent':True,
                 'zero_threshold_empty_support_accepted':True,
                 'limit':'Input booleans/labels have no origin binding; distinct labels alone do not prove independent evidence.'})


def individual(i, generation=0, parents=(), score=0.5, latency=10.0, cost=100, delta=''):
    return pciv.Individual(i,generation,pciv.Genotype(i,'Return the value for J=1',1,6),
                           pciv.Phenotype(latency,cost,score,delta),parents)


parent = individual(1)
adapted = pciv.LamarckianEngine().retro_inherit(parent)
assert adapted.genotype == parent.genotype
assert adapted.phenotype.correctness_score == 0.55 and adapted.phenotype.latency_ms == 9.5
assert adapted.phenotype.token_cost == 105
controls.append({'id':'synthetic_improvement','same_genotype':True,'score_before':0.5,'score_after':0.55,
                 'latency_before':10.0,'latency_after':9.5,'cost_before':100,'cost_after':105,
                 'limit':'No task execution or model measurement occurs, even for an empty reflection delta.'})
changed = pciv.MutationForge().point_mutate(parent.genotype,('J=1','J=2'))
assert changed.template == 'Return the value for J=2'
controls.append({'id':'unprotected_task_edit','before':parent.genotype.template,'after':changed.template,
                 'limit':'No protected-span or semantic-equivalence argument exists in this toy forge API.'})

best = individual(9,score=0.9,latency=1,cost=1)
dominated_same_id = individual(9,score=0.1,latency=20,cost=200)
dominated_distinct = individual(10,score=0.1,latency=20,cost=200)
selector = pciv.ParetoSelector()
assert len(selector.extract_pareto_front([best,dominated_same_id])) == 2
assert selector.extract_pareto_front([best,dominated_distinct]) == [best]
controls.append({'id':'duplicate_identity_frontier','same_id_dominated_member_retained':True,
                 'distinct_id_positive_control_excluded':True,
                 'limit':'The standalone list selector assumes unique identities; no boundary validates that premise.'})

dag = pciv.LineageDAG()
dag.add_individual(individual(1))
tracker = pciv.LineageTaintTracker(dag)
tracker.mark_tainted(1)
dag.add_individual(individual(2,1,(1,)))
assert not tracker.is_quarantined(2)
assert tracker.mark_tainted(1) == {1,2} and tracker.is_quarantined(2)
islands = pciv.IslandEcology(['A','B'],capacity_per_island=1)
islands.populate('A',dag.individuals[1]);islands.populate('B',dag.individuals[2])
assert islands.migrate('A','B',1) and len(islands.islands['B']) == 2
assert not islands.migrate('missing','B',1)
controls.append({'id':'snapshot_taint_and_capacity','later_child_initially_quarantined':False,
                 'explicit_rescan_marks_child':True,'destination_size':2,'declared_capacity':1,
                 'quarantined_source_can_migrate':True,'invalid_island_control_refused':True,
                 'limit':'These isolated classes have no shared custody integration; a caller may add guards, but none is supplied here.'})

log = pciv.PromptCivilizationEventLog()
log.append_event('A',{'value':1});log.append_event('B',{'value':2})
assert log.verify_integrity()
head = log.last_hash
log.events.pop()
assert log.last_hash == head and log.last_hash != log.events[-1]['hash'] and log.verify_integrity()
log.events[0]['data']['value'] = 99
assert not log.verify_integrity()
controls.append({'id':'tail_truncation','truncated_prefix_accepted':True,'stored_head_mismatch_ignored':True,
                 'ordinary_payload_tamper_refused':True,
                 'limit':'Internal chain consistency is narrower than append-only authenticated history; no cryptographic collision is claimed.'})

# Complete small ordered DAG population: independent transitive-closure oracle.
edges = [(i,j) for i in range(4) for j in range(i+1,4)]
closure_checks = 0
for mask in range(1<<len(edges)):
    selected = [edge for k,edge in enumerate(edges) if mask & (1<<k)]
    graph = pciv.LineageDAG()
    for i in range(4):graph.add_individual(individual(i,i,tuple(a for a,b in selected if b==i)))
    reachable = [[(i,j) in selected for j in range(4)] for i in range(4)]
    for k in range(4):
        for i in range(4):
            for j in range(4):reachable[i][j] |= reachable[i][k] and reachable[k][j]
    assert graph.is_acyclic()
    for i in range(4):
        assert graph.get_descendants(i) == {j for j in range(4) if reachable[i][j]}
        assert graph.get_ancestors(i) == {j for j in range(4) if reachable[j][i]}
        closure_checks += 2
controls.append({'id':'ordered_dag_positive','graphs':64,'ancestor_descendant_comparisons':closure_checks,
                 'limit':'All four-vertex forward-edge DAGs under this fixed order; no authenticated causality or arbitrary external mutation claim.'})

two = pciv.LineageDAG()
two.add_individual(individual(1));two.add_individual(individual(2,1,(1,)))
ranks = pciv.LineagePageRank().compute_ranks(two)
expected = (Q(37,57),Q(20,57))
transition = ((Q(1,2),Q(1,2)),(Q(1),Q(0)))
rhs = tuple(Q(17,20)*sum(transition[j][i]*expected[j] for j in range(2))+Q(3,40) for i in range(2))
assert rhs == expected and all(abs(ranks[i+1]-float(expected[i]))<1e-12 for i in range(2))
controls.append({'id':'inverse_rank_positive','reported':ranks,'exact_two_node_fixed_point':list(map(str,expected)),
                 'max_error':max(abs(ranks[i+1]-float(expected[i])) for i in range(2)),
                 'limit':'For this graph, normalized leaky iteration agrees with the uniform dangling-node PageRank equation. Finite iterations/floats are not an arbitrary-graph exact certificate.'})


def ev(owner):
    return {'path':owner['current_path'],'sha256':owner['current_sha256']}


findings = [
 {'id':'MEP-F01','severity':'high','statement':'LamarckianEngine prescribes better correctness and latency without evaluating the changed prompt; an empty reflection keeps the exact genotype but still moves score0.5 to0.55 and latency10 to9.5. Its retained test asserts this manufactured improvement. These fields cannot be used as empirical workflow outcomes.','evidence':[ev(pciv_owner)],'recommended_action':'Keep synthetic dynamics explicitly separated from measured results; require an independent held-out evaluation and actual usage/time receipts for benchmark comparisons.'},
 {'id':'MEP-F02','severity':'medium','statement':'The toy forge can change the task itself, with no protected-span input or semantic-preservation witness. A public J=1 to J=2 mutation is accepted. Token edits and appended reflection text are not an implementation of the protected-core contract.','evidence':[ev(pciv_owner)],'recommended_action':'Bind immutable task material and a scoped preservation check before exposing these mutation operators to the shared-seed benchmark.'},
 {'id':'MEP-F03','severity':'medium','statement':'The EIS toy ExternalAdmissionBoundary returns admitted=True after byte/substring screening and never consults its supplied thymus or an external decision. TwoSignalGuard trusts its Boolean input, and SupportPolicy accepts empty support when configured with zero. These are toy filtering/counting policies, not authenticated admission or independent-evidence enforcement.','evidence':[ev(eis_owner)],'recommended_action':'Use screening-specific result names and explicit admitted-parameter/witness boundaries; keep this simulation separate from actual authorization.'},
 {'id':'MEP-F04','severity':'medium','statement':'The standalone Pareto list selector skips comparisons for equal IDs, so a strictly dominated duplicate-ID member remains on the returned frontier. A distinct-ID control is correctly removed.','evidence':[ev(pciv_owner)],'recommended_action':'Validate unique candidate identity before selection or compare the intended occurrence identity explicitly.'},
 {'id':'MEP-F05','severity':'medium','statement':'Taint is a snapshot set, and later children stay unquarantined until an explicit rescan. Island migration does not consult that set or enforce its stored capacity; a quarantined source moves into a full capacity-one target, leaving two members. No integrated fail-closed quarantine/capacity workflow follows from these classes.','evidence':[ev(pciv_owner)],'recommended_action':'Declare update-time taint and admission checks and enforce target capacity before state changes if these demos are adapted into workflows.'},
 {'id':'MEP-F06','severity':'medium','statement':'The event-log verifier accepts a truncated prefix while last_hash still names the removed tail. It verifies only surviving links/data, not the retained head, expected length, durable storage or an external anchor. Ordinary payload tampering is detected.','evidence':[ev(pciv_owner)],'recommended_action':'Check the bound expected head and sequence/length, and distinguish local chain consistency from durable authenticated append-only history.'}
]
claims = [
 {'id':'MEP-C01','statement':'The admitted teaching DAG has concrete parent-existence/generation checks and graph traversal. All64 four-vertex forward-edge DAGs pass512 independent ancestor/descendant comparisons. This supports bounded reachability behavior, not authenticity of the declared causal graph.','evidence':[ev(pciv_owner)]},
 {'id':'MEP-C02','statement':'The small inverse-lineage rank example agrees with an exact two-node stationary equation under uniform dangling redistribution. Mixed-direction Pareto comparisons also correctly exclude a strictly dominated distinct-ID control. These are mathematical toy mechanisms; they establish no model improvement.','evidence':[ev(pciv_owner)]},
 {'id':'MEP-C03','statement':'The EIS fixture gate actually calls a supplied detector on retained positive/negative examples and rejects an empty polarity side; the byte filter, substring match and caller-count policies are explicit finite computations. They offer useful baseline components when their evidence and authority limits are preserved.','evidence':[ev(eis_owner)]}
]
result = {'source_commit':'8050c66900899771766f33e8f5fdd200b7dd9120',
 'status':'complete_twelve_migrated_original_source_reviews','file_reviews':rows,
 'claims':claims,'findings':findings,'controls':controls,
 'workflow_disposition':'Scoped teaching references only. Any shared-seed adaptation must replace simulated fitness, bind task preservation and supply independent evaluation/custody guards.',
 'limits':['Twelve original source bodies fully read; both current READMEs and their original recovery members also read.',
           'Only the two fully reviewed standard-library toy modules and nine public control groups ran. No original-source edit, pytest/native/provider or private benchmark access.',
           'Control comparisons are not independent model trials. No biological or real-world causality claim follows.']}
path = REV/'additional_migrated_eis_pciv_teaching.json'
path.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'full_original_bodies':len(rows),'control_groups':len(controls),'claims':len(claims),'findings':len(findings),'report_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}))
