"""Record the actually read crosswalk; retain conditional mathematical boundaries."""
import sys
sys.dont_write_bytecode=True
import additional_pfp_adapters_audit as a

a.record({'genesis_crosswalk.md': (
    'Read all 8354 numbered lines, including the repeated stage envelopes; no deduplication scan was credited as source reading. '
    'This is a secondary, explicitly CROSSWALK_DRAFT and AuthorityEffect=None compendium, not an external derivation or authority transfer. '
    'GEN000 treats <> as an inscription; separated tokens, carriers, metrics, categories, probability laws and physical interpretations are added assumptions. '
    'The exact Gram/Sylvester positive-definite criterion is valid for a nondegenerate finite Euclidean simplex under declared rational distances; a positive determinant alone is insufficient. '
    'Weighted-l1 primal/dual equality gives an exact finite optimum under the stated linear constraints and positive weights; closed/nonexact cochains differ from nonclosed curvature. '
    'Ordered nonabelian holonomy requires connector/order conventions and does not reduce to scalar angle closure. '
    'GEN022 onward repeatedly limits candidate tags to syntactic well-formedness and leaves semantic models and independent checkers as future work. '
    'Category/coherence, causal intervention, probability, Hilbert/Born/tensor, gravity and algorithmic-hardness descriptions are conditional obligations, not derivations from the primitive inscription. '
    'Finite session reachability is weaker than universal termination; blind joint weights require normalization; manifold claims require vertex links; Bianchi identities require compatible transports/order. These boundaries are tested separately against the stage code. '
    'Exact cancellation needs a supplied complete finite sector family; sampling and interval statements need a declared distribution and distinguish sufficient bounds from necessary coverage. '
    'Hashes, references and test links establish only the binding actually enforced, not provenance, adequacy, independence or completion. '
    'GEN098 explicitly requires independent implementations, GEN099 preserves a fixed failure predicate under shrinking, and GEN100 requires tests or typed unresolved obligations without claiming a closed horizon. '
    'No linked sealed seed, answer, private material or external source was opened. Local source reading and the retained Python checker replays cannot grade those external repositories.'
)})
n=a.read('_notes.json');by={r['path']:r for r in a.read('_scope.json')['files']}
def evidence(path,start,end):
    return {'path':path,'sha256':by[path]['sha256'],'lines':[start,end]}
initial_ranges={
    'ADAPT-F01':[(116,136),(176,184),(221,234)],
    'ADAPT-F02':[(22,133)],
    'ADAPT-F03':[(44,67)],
    'ADAPT-F04':[(16,41)],
    'ADAPT-F05':[(33,78)],
}
for f in n['findings']:
    if f['id'] in initial_ranges:f['source_ranges']=[evidence(f['sources'][0],lo,hi) for lo,hi in initial_ranges[f['id']]]
    if f['id']=='ADAPT-F25':f['source_ranges'].append(evidence(f['sources'][0],155,173))
    if f.get('control','').startswith('_'):f['control']='dag/reviews/additional_pfp_adapters'+f['control']
for c in n['claims']:
    if c['id']=='ADAPT-C01':
        c['source_ranges']=[evidence(c['sources'][0],39,174),evidence(c['sources'][1],227,307),evidence(c['sources'][1],324,423)]
    else:c['source_ranges']=[evidence(c['sources'][0],96,174)]
    if c.get('control','').startswith('_'):c['control']='dag/reviews/additional_pfp_adapters'+c['control']
n['findings'].append({
    'id':'ADAPT-F26',
    'claim':'The catalog binds demo_cohomology_battery to a stale fixture SHA-256. The current fixture matches the frozen original inventory but not this declared catalog digest; the other 133 catalog fixture hashes match.',
    'sources':['pfp/infrastructure/adapters/mssn_research/catalog.json','pfp/infrastructure/adapters/mssn_research/fixtures/demo_cohomology_battery.json'],
    'source_ranges':[evidence('pfp/infrastructure/adapters/mssn_research/catalog.json',445,446)],
    'control':'dag/reviews/additional_pfp_adapters_automated.json:catalog_fixture_bindings',
    'limits':'Bounded JSON/reference assessment, not a full catalog/fixture body read. No native scenario execution or runtime impact claimed.'
})
n['family_assessments']=[
    {'family':'Host, native and injected adapters','assessment':'Some adapters enforce typed envelope fields; others coerce values or omit action/case binding. Native kernels and unavailable dependencies were not built or used. An injected malformed outcome exposes an adapter boundary without proving the canonical host produces it.'},
    {'family':'101 MSS stage checkers','assessment':'All checker bodies and preamble were read. They decide restricted finite predicates over declared data and axioms. PASS may validate a negative, obstruction or out-of-scope certificate rather than the positive domain claim. The 1033 supplied cases are regression observations; independently authored controls expose both false acceptance relative to broader prose and deliberately incomplete certificate policies.'},
    {'family':'Finite exact mathematics','assessment':'Exact graph parity, finite involution cancellation, rational matrix identities and finite algebra checks have useful conditional content. Input completeness, chosen grammar, orientation, normalization, manifold validity and source interpretation remain distinct obligations. A finite calculation is not a derivation of a physical law.'},
    {'family':'Evidence, replay, budgets and sandbox boundaries','assessment':'Digests bind only encoded fields; a locally recomputed head is not an externally authenticated root. In-process restrictions and copied subprocess packages are not OS isolation. Scripted fixture success and supplied coverage strings are not empirical learning or provider execution evidence. Source bodies were read without launching models, providers, historical migrations or broad native builds.'},
    {'family':'Genesis crosswalk','sources':['pfp/infrastructure/adapters/mssn_research/genesis_crosswalk.md'],'source_ranges':[evidence('pfp/infrastructure/adapters/mssn_research/genesis_crosswalk.md',1,8354)],'assessment':'All 101 stage notes were read literally. The compendium explicitly withholds derivation/authority claims, separates wire syntax from semantic obligations, and requires future typed transports and independent checkers. Linked external/sealed sources were not followed. Its local predicates must still be constrained by the actual checker findings in this report.'},
    {'family':'Generated/configuration/fixture JSON','assessment':'138 schema-specific parsed assessments remain full_source_read=false. Byte pins, indices, dimensions, references and exact bounded finite gauge enumeration were evaluated where appropriate. Most expected result fields remain supplied ground truth. One catalog fixture pin is stale; no original artifact was repaired.'}
]
for c in n['controls']:c['sha256']=a.sha(a.ROOT/c['path'])
a.write('_notes.json',n);a.report()
