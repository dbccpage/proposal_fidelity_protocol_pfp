"""Persist substantive HoTT source assessments; pending bodies remain explicit."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REV = ROOT / 'dag/reviews'
PREFIX = 'additional_rust_hott_remaining'
scope_path = REV / (PREFIX + '_scope.json')
scope = json.loads(scope_path.read_text())
by = {Path(r['path']).name: r for r in scope['files']}
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
notes = {
    'a_infinity.rs': 'Complete1443-line body read in four numbered ranges, including all explanatory text, algorithms and tests. Entire module disabled by cfg(any()) with missing legacy Parity import. Ring traits impose no laws; i64 unchecked operations and f64 approximate zero are not exact unrestricted ring semantics. Generic A-infinity interfaces have only supplied n1/n2/n3 checks, not full degree/multilinearity/higher-law admission. Morphism composition handles f1/f2, substitutes B::default for the actual intermediate algebra, and inherits zero higher components. Massey routine verifies cycles and chosen boundary equations but uses a DGA formula for generic A-infinity inputs, never checks the output cycle, and leaves indeterminacy empty. Formality checker wrongly promotes nonzero m3 to NotFormal, skips repeated triples when fewer than3 supplied cycles and only takes one higher tuple. Truncated polynomial/exterior algorithms are useful ordinary algebra drafts on well-formed exact inputs; no dimension/grading normalization or homogeneous-input admission, exterior dimension is unused and repeated merge previews are discarded. Massey tests never call the routine, one asserts true; sign test contradicts its own exponent at(1,2,0). Independent F2 algebra/isomorphism countermodel disproves the retained formality criterion. No original code compiled/executed.',
    'substitution.rs': 'Complete317-line body read including capacity boilerplate/tests. Entire module disabled by cfg(any()) and imports missing super::term::Term. Dormant de Bruijn substitution removes a variable, decrements higher indices and shifts the replacement under binders; recursive branches for listed eliminators are present. Raw shift uses unchecked signed cast/add/backcast and cutoff+1, with no scope/overflow admission, so invalid negative shifts can wrap; term representation/type annotations are an unreviewed dependency. No substantive substitution tests here, only disabled count/capacity tests. No active capture-avoidance kernel or runtime claim.',
    'presentation_difference.rs': 'Complete433-line body read. Constructor/serde admission checks nonempty duplicate-free carrier, unique question IDs and complete answer lengths. Profiles define an exact finite equivalence; derived-question predicate is constancy on parent fibers. Extension evaluator requires exact carrier and prefix-preserved old questions, added question, retained/protected active pair and strict class-count increase. This is useful finite distinction bookkeeping under admitted inputs, not discovery/truth of new questions. All public fields and public evaluation DTO bypass those constructors; evaluator does not revalidate. Missing child profile is treated as not zero-related while partition silently skips it, enabling malformed child acceptance. Demand Deserialize bypasses off-diagonal constructor; authority_effect override is merely caller metadata. Hashes bind serialization, not causal provenance. Sole inline mutation test literal Ok/Err; external integration target not read here.',
    'primitive_difference.rs': 'Complete802-line source/prose/test body read in two numbered ranges. Raw carrier snapshots one supplied zero relation, checks reflexivity/symmetry and exact representative-block equivalence in quadratic storage/time, with actual failure triple. Private validated carrier stores reps/classes and brand, gates delta congruence/factor access, and separately snapshots observables for representative constancy and joint descent. For stable mathematical callbacks and lawful equality, these are exact finite mechanisms; both components descend iff the pair descends, and LGGR explicitly means one passes while another fails, not cohomology. DeltaFactor stores a live reference and calls delta again after admission, so interior-mutability changes can invalidate the factorization. Public count-only witness DTOs are forgeable but do not themselves bypass private carrier construction. Brand counter is process-local u64 metadata, no cryptographic/cross-process identity; uniqueness assumes no wrap. Checked n² arithmetic is not a memory/time budget. Diagnostic out-of-domain classification is expressly not a quotient theorem. Embedded substantive tests and call counts read but not run; stated missing finite Lean bridge remains an obligation, not newly verified absence.',
    'higher_inductive_type.rs': 'Complete264-line body read. Public finite point/path specification with circle/interval examples and caller truncation tag. is_well_formed checks endpoints only; no constructor-name/dimension/globularity/eliminator admission. CycleRank strengthens unique point names, endpoint membership and64/128 size bounds, then computes undirected multigraph E-V+components via union-find. It treats every path record as an edge regardless of dimension, so higher cells can inflate the advertised1-skeleton rank. This graph invariant does not establish a HIT homotopy type. All tests/capacity metadata read.',
    'quasi_category.rs': 'Complete383-line body read including all tests/capacity code. Entire module disabled by cfg(any()); legacy simplicial-set import unresolved in this active crate. Dormant verify unconditionally sets true. Composition uses vertex triples rather than actual face maps and cannot distinguish parallel arrows; hom excludes degenerate identity edges, and homotopy_category_rank counts raw nondegenerate edges without quotienting homotopies. Proposed nerve builds only dimensions0..2 from endpoint pairs, with no actual category laws/full simplicial admission. Euler text confuses homotopy-group cardinalities with ordinary alternating simplex counts. These are dormant draft gaps, not active runtime failures. Formal quasi-category definition separately checked in Lurie1.1.2.4; no dependency source/native execution credit.',
    'Cargo.toml': 'Complete19-line manifest read. Edition2021, workspace version/license, five third-party dependencies; autotests=false with one explicit sibling presentation_difference integration target. No dependency source, external test body, Cargo build or Rust execution credit.',
    'lib.rs': 'Complete118-line body read. Crate explicitly describes finite records rather than proof-assistant kernel; exports separate finite primitive-difference/presentation owners and shape records. PathConcatWitness checks two nonempty integer sequences meet and adds checked step counts; it verifies neither graph adjacency nor identity inhabitants. Mutation-count comment is historical declaration. Full embedded test read, not run.',
    'empty_type.rs': 'Complete127-line body read. EmptyType is explicitly a name-only shape; EmptyCardinal checks supplied equations n+0=n and n*0=0 after nonempty ID admission. No actual empty carrier/eliminator or type formation proof. Exact scalar invariant and all tests read, no native execution.',
    'unit_type.rs': 'Complete103-line body read. UnitType validates two nonempty references only. Private UnitEliminationWitness checks declared inhabitant count1 and declared maps_into_carrier=carrier_points; it constructs neither carrier, maps, unique inhabitant nor elimination. Zero target count is permitted correctly at scalar level. All tests read.',
    'type_universe.rs': 'Complete116-line body read. Explicitly not a cumulative hierarchy kernel: a universe is a nonempty name plus u32 level. CumulativityWitness enforces strict numeric term_level<universe.level and checked gap, without terms, typing judgments or embeddings. No test covers this appended numeric witness in this body; existing shape tests read.',
    'type_formation.rs': 'Complete167-line body read. TypeRecord is a public ID/tag/level record; validation checks ID only. CumulativeFormer supplies numeric level formulas: Pi exactly max(domain,family), identity exactly base, unit any declared>=base. No actual terms/families/dependent formation rules admitted. Exact-minimum Pi convention is narrower than arbitrary cumulative placement, not a false arithmetic result. All tests read.',
    'pi_type.rs': 'Complete114-line body read. Explicit opaque base/family name record. PiCardinalityWitness checked-multiplies supplied u64 fiber sizes; empty product1 and zero fibers handled, but an overflowing prefix before a later zero is refused despite final mathematical product0. This is conservative/order-sensitive refusal, not an unsound accepted cardinality. No connection between supplied sizes and real fibers; appended witness has no test in this body.',
    'sigma_type.rs': 'Complete137-line body read. Opaque base/family shell, separate FiniteSigma sums at most32 supplied u32 fiber sizes in u128, including empty sum0. No actual dependent pair carrier or binding to SigmaType. Given the size/input bounds, sum cannot approach u128 overflow. All shape/count tests read.',
    'sum_type.rs': 'Complete138-line body read. Opaque two-name sum shell. CoproductPoint encodes bounded left indices and arbitrary representable right offsets; no right cardinality or stored left boundary. Roundtrip needs the same supplied left_card; this is ordinal offset encoding, not admission to a fixed finite coproduct. Right overflow refused. All tests read.',
    'identity.rs': 'Complete127-line body read. IdentityType checks nonempty type/term names, difference/certificate shape and matching difference_ref. It never matches left/right to difference source/target, dereferences a checker, proves zero or admits terms in the named type. Transport and TransportAuth check nonempty refs only; optional loss ledger unchecked. The dependent-type wording is interpretive metadata, not kernel semantics. Embedded single happy-path test read.',
    'path.rs': 'Complete222-line body read. Path explicitly shape-only; from_identity intentionally does not validate its input. IntegerPath separately permits every ordered pair of u64 endpoints, inverse swap and endpoint-matching composition; this gives pair-groupoid-style endpoint bookkeeping, not equality of distinct points in a discrete type. No adjacency, length or dependent transport is represented. All tests read.',
    'path_transport.rs': 'Complete173-line body read. Transport alias and J-style eliminator explicitly shape-only, no elimination computation. ReducedIntegerPath genuinely cancels adjacent opposite +/-1 steps, computes checked signed displacement and translates a supplied i64 value; inverse reconstruction checks zero combined displacement. Overflow correctly refuses out-of-range transport. This is one-generator integer arithmetic, not arbitrary HoTT path induction. Tests read.',
    'difference.rs': 'Complete117-line body read. Difference trait imposes no laws; DifferenceTerm and ZeroDifferenceCertificate validate nonempty refs only. ContextualDifferenceWitness declares failed transport solely from unequal nonempty before/after reference names, ignoring endpoints/context and actual difference values. IntegerDifference separately computes checked target-source and reconstructs target exactly. No derivation of logic, types or sameness from an unqualified primitive is implemented. Full test body read.',
    'contractible_type.rs': 'Complete100-line body read. Explicitly says it records references and does not prove contractibility. ContractionWitness adds declared counts centers=1,points>0,paths=points; no endpoints or coverage show every point contracts to the center. These are count constraints, not isContr. Full shape/count tests read; no mutation execution.',
    'truncation.rs': 'Complete151-line body read. TruncationLevel and terminal outcomes are tags; no truncation operation/h-level proof. AuthorityType accepts Authority payload even empty if subject/proof refs nonempty, without checking proof or subject binding. RefusalType admits Refusal/BudgetUnknown/OracleNeeded tags only; packet validator checks five refs and ignores layer/truncation semantics. These are public declared records, not actual authority issuance or a dependent-type kernel. Tests read.',
    'univalence_witness.rs': 'Complete160-line body read. Strong explicit nonclaim: shape-only nonempty universe/proof refs do not prove univalence. FiniteTransport separately requires equal finite ordinal sizes, in-range maps and backward(forward(i))=i for every i. On equal finite sets this implies bijection and the other roundtrip; omission of an explicit forward(backward(i)) loop is not a defect. Empty carriers admitted. The returned witness stores cardinality only, not maps or their identity. All tests read.',
    'tower.rs': 'Complete110-line body read. Six canonical enum labels and descriptive HoTT roles, with exact ordered list admission and nonempty carrier/policy/eliminator refs. No maps/coherence/limit/tower mathematics or runtime authority checked. Sole mutation-named test constructs literal Ok/Err and never calls this owner. Source declaration killed=6 is not reproduced evidence.',
    'hott_contract_alignment.rs': 'Complete165-line body read. Six default concept/URN/stratum declarations; census enforces active rows, nonempty concepts, URN prefix, uniqueness, count6 and presence of truncation URN. It does not check canonical concept-to-URN mapping, known remaining URNs, mechanization_stratum or actual contract contents. Useful table census only, despite formal-mapping headline. All tests read; no contract-source or mutation credit.',
}

def ev(name, low, high):
    row = by[name]
    return {'path': row['path'], 'sha256': row['sha256'], 'lines': [[low, high]]}

claims = [
    {'id': 'RHT-C01', 'statement': 'Most HoTT type formers explicitly provide finite shape records rather than a proof-assistant kernel. Nonempty labels and numerical census conditions cannot supply inhabited identity, dependent elimination, contractibility, cumulative universes or univalence. The source contains clear nonclaims that should be preserved.',
     'source_evidence': [ev('lib.rs', 1, 12), ev('contractible_type.rs', 1, 5), ev('path_transport.rs', 1, 6), ev('univalence_witness.rs', 1, 32)]},
    {'id': 'RHT-C02', 'statement': 'The arithmetic helpers have useful exact restricted meanings: checked fiber products/sums, finite ordinal offset encoding, endpoint composition, cancellation of one-generator inverse steps and checked integer translation. Their supplied cardinalities, coordinates and labels are premises; no link to arbitrary semantic queries or dependent types follows.',
     'source_evidence': [ev('pi_type.rs', 74, 114), ev('sigma_type.rs', 98, 115), ev('sum_type.rs', 98, 125), ev('path.rs', 142, 176), ev('path_transport.rs', 100, 153)]},
    {'id': 'RHT-C03', 'statement': 'FiniteTransport checks bounded total maps f,g on the same finite ordinal and g(f(i))=i for every point. This makes f injective, hence surjective on the equal finite carriers, so also f(g(i))=i. It therefore establishes the stipulated mutual-inverse property, including the empty case; it does not establish univalence or retain a binding to the particular maps.',
     'source_evidence': [ev('univalence_witness.rs', 76, 150)]},
    {'id': 'RHT-C04', 'statement': 'The HIT helper computes the cycle-space rank E-V+components of the supplied finite endpoint multigraph, with duplicate-point and endpoint admission. This is useful for genuine1-cell inventories, including loops and disconnected graphs. Higher-cell dimensions and attaching maps require a separate representation/admission before interpreting the value as topology.',
     'source_evidence': [ev('higher_inductive_type.rs', 120, 240)]},
    {'id': 'RHT-C05', 'statement': 'On stable supplied callbacks and ordinary equality, the primitive-difference owner checks an exact finite equivalence relation, constructs its quotient and tests delta/observable constancy on classes. The representative-table delta test is equivalent to constancy on every pair of quotient fibers. Joint observable descent is precisely the conjunction of individual descent; the documented local-green/global-red case has one descending component and another failing component. No cohomological or global physical claim follows.',
     'source_evidence': [ev('primitive_difference.rs', 189, 285), ev('primitive_difference.rs', 353, 398), ev('primitive_difference.rs', 402, 493)]},
    {'id': 'RHT-C06', 'statement': 'For well-formed immutable presentation inputs, preserving every old question and adjoining a question that separates an old fiber strictly refines the profile partition. Derived questions, defined as functions of old profiles, cannot split those fibers. The evaluator usefully distinguishes this finite information gain from redundant questions; it takes all answers and retained/protected demands as supplied premises.',
     'source_evidence': [ev('presentation_difference.rs', 119, 160), ev('presentation_difference.rs', 182, 209), ev('presentation_difference.rs', 340, 415)]},
    {'id': 'RHT-C07', 'statement': 'The retained A-infinity source contains ordinary polynomial/exterior multiplication algorithms and selected algebraic identities, but its entire module is disabled. General A-infinity, morphism, formality and Massey claims require substantially more than these examples. The audit supplies an exact finite F2 countermodel with all potentially nonzero identities checked on a basis and an explicit algebraic argument for the remaining arities; this is independent mathematics, not Rust execution.',
     'source_evidence': [ev('a_infinity.rs', 1, 3), ev('a_infinity.rs', 654, 678), ev('a_infinity.rs', 858, 981), ev('a_infinity.rs', 1062, 1125)]},
]
findings = [
    {'id': 'RHT-F08', 'statement': 'Dormant ComposedAInfinityMorphism implements only f1/f2 and inherits zero f_n for n>=3. Even composition with a strict identity destroys a valid nonzero f3: on a zero-operation graded algebra with a in degree0 and b in degree-2, choose f1=id and f3(a,a,a)=b. All morphism equations vanish, but the implemented composite has third component0. B::default also fails to bind the actual parameterized middle algebra. This is a design counterexample in disabled source.',
     'source_evidence': [ev('a_infinity.rs', 235, 251), ev('a_infinity.rs', 288, 319)], 'control': 'RHT-P10'},
    {'id': 'RHT-F09', 'statement': 'The dormant formality checker returns NotFormal for any nonzero m3 on supplied cocycles, without cohomology/gauge comparison. This is mathematically false even for valid minimal A-infinity data. An exact F2 example has triangular graded basis e1,e2,u (degrees0,0,-1), m3 equal to the Hochschild coboundary of h2(e1,e1)=u, and explicit inverse A-infinity morphisms (id,h2) to the strict d=0 algebra. It is formal while m3(e1,e1,e1)=u triggers NotFormal. Independent controls check726 algebra identities,2184 two-way morphism identities and120 inverse-composition basis cases; multilinearity and arity bounds cover all remaining inputs/identities. The source also omits repeated triples for fewer than3 supplied cycles and checks only one tuple per higher arity.',
     'source_evidence': [ev('a_infinity.rs', 456, 540)], 'control': 'RHT-P11',
     'limits': 'Standard nonunital A-infinity equations over F2; source interface imposes no strict-unit condition. This is an exact independent countermodel, not an executed Rust verdict.'},
    {'id': 'RHT-F10', 'statement': 'The dormant Massey routine accepts a generic AInfinityAlgebra but uses the strict-DGA representative s*c+(-1)^(|a|+1)*a*t. Given cycles and ds=a*b,dt=b*c, Leibniz makes its differential (a*b)*c-a*(b*c), which need not vanish in a non-strict A-infinity algebra. It neither restricts to an admitted DGA nor adds/checks the higher correction; it also returns empty uncomputed indeterminacy. Its embedded Massey tests never call compute and include assert(true). These facts leave the promised representative-cocycle/coset claim unestablished.',
     'source_evidence': [ev('a_infinity.rs', 354, 450), ev('a_infinity.rs', 1263, 1305)]},
    {'id': 'RHT-F11', 'statement': 'The disabled A-infinity sign test expects-1 from (-1)^(r*s+t) at(r,s,t)=(1,2,0), whose exponent is2 and value+1. Its displayed rs+t convention also gives the opposite binary-associator signs from check_n3. The implemented n3 expression matches a standard r+s*t convention instead. A consistent convention and substantive nonzero-differential/higher-operation tests are needed before this draft can be enabled.',
     'source_evidence': [ev('a_infinity.rs', 152, 159), ev('a_infinity.rs', 1081, 1124), ev('a_infinity.rs', 1395, 1415)], 'control': 'RHT-P12'},
    {'id': 'RHT-F06', 'statement': 'evaluate_extension accepts public malformed presentations without rechecking complete answer tables. Parent points[a,b,c] with no questions has one class. A child with the same points and one question carrying only answers[0,1] has no profile for c; zero_related(a,c) returns false and partition silently drops c. A retained/protected demand(a,c) is marked Resolved and accepted because the remaining two classes exceed one, although the child never answered c. Constructor/serde admission would refuse this input; public fields and the evaluator permit the bypass.',
     'source_evidence': [ev('presentation_difference.rs', 91, 97), ev('presentation_difference.rs', 182, 205), ev('presentation_difference.rs', 304, 311), ev('presentation_difference.rs', 360, 415)]},
    {'id': 'RHT-F07', 'statement': 'DeltaFactor does not retain the validated delta table; apply calls the live provider again. With a two-point universal zero relation, delta initially constant0 passes congruence. If an interior-mutable provider later changes delta(x,y) to x, the stored single quotient class still evaluates through representative0 while delta(1,0)=1. The issued factor no longer factors the current delta. Stable callback semantics are an essential unstated runtime premise; cache/freeze the admitted values or enforce/recheck a versioned provider boundary. This is an independent source-model counterexample, not a compiled Rust reproduction.',
     'source_evidence': [ev('primitive_difference.rs', 34, 49), ev('primitive_difference.rs', 353, 399), ev('primitive_difference.rs', 497, 519), ev('primitive_difference.rs', 732, 758)]},
    {'id': 'RHT-F04', 'statement': 'cycle_rank ignores PathConstructor.dimension while claiming to measure the1-skeleton. A single point with a sole dimension2 self-record is counted as one edge and returns rank1. No dimension1 generator was supplied. The helper should admit/filter a genuine1-cell inventory; its current graph calculation cannot support the higher-dimensional interpretation.',
     'source_evidence': [ev('higher_inductive_type.rs', 22, 38), ev('higher_inductive_type.rs', 164, 200)]},
    {'id': 'RHT-F05', 'statement': 'The quasi-category module is entirely disabled by cfg(any()). Its dormant verify simply returns true, without checking simplicial identities or any inner horn. Later draft composition uses vertex lists instead of face incidences, and homotopy_category_rank omits identities and takes no homotopy quotient. This is retained proposal text, not an implemented quasi-category checker; the unrelated capacity record is disabled too.',
     'source_evidence': [ev('quasi_category.rs', 1, 2), ev('quasi_category.rs', 91, 96), ev('quasi_category.rs', 108, 165)]},
    {'id': 'RHT-F01', 'statement': 'IdentityType::validate compares only difference_ref with certificate.difference_ref. A record for left=x,right=y accepts a shaped difference whose endpoints are unrelated u,v. Even structural subject binding is missing; its certificate refs also are not dereferenced. This is a shape-layer gap, not a demonstrated authority bypass.',
     'source_evidence': [ev('identity.rs', 23, 34), ev('difference.rs', 28, 60)]},
    {'id': 'RHT-F02', 'statement': 'ContextualDifferenceWitness::is_failed_transport_witness returns true from different nonempty before/after names alone, even with empty left/right/context and no differing values. Two names for equal difference values suffice. This is a reference-change predicate, not a proof of failed congruence/transport.',
     'source_evidence': [ev('difference.rs', 63, 78)]},
    {'id': 'RHT-F03', 'statement': 'certify_hott_binding_table can accept six arbitrary unique concepts/URNs, provided every URN has the prefix and one is the truncation URN. Swapping canonical concept-to-URN associations or using arbitrary mechanization strata also passes. It certifies the implemented census, not the headline formal mapping to canonical contracts.',
     'source_evidence': [ev('hott_contract_alignment.rs', 1, 4), ev('hott_contract_alignment.rs', 108, 139)]},
]
ledger = json.loads((REV / (PREFIX + '_read_ledger.json')).read_text())
reviews = []
for name, note in notes.items():
    row = by[name]
    raw = (ROOT / row['path']).read_bytes()
    assert sha(ROOT / row['path']) == row['sha256']
    n = len(raw.decode('utf8').splitlines())
    displayed = set()
    for entry in ledger:
        if entry['path'] == row['path']:
            assert entry['sha256'] == row['sha256']
            for lo, hi in entry['displayed_lines']:
                displayed.update(range(lo, hi + 1))
    assert set(range(1, n + 1)) <= displayed
    reviews.append({'path': row['path'], 'sha256': row['sha256'], 'full_source_read': True,
                    'reviewed_lines': [[1, n]], 'source_line_count': n, 'reviewer': 'parent',
                    'reading_method': 'Complete numbered body display and manual assessment; no template transfer.',
                    'assessment': note})
pending = sorted(row['path'] for name, row in by.items() if name not in notes)
report = {'schema_version': '1.0', 'status': 'in_progress' if pending else 'complete',
          'source_commit': scope['source_commit'], 'scope_manifest': scope_path.relative_to(ROOT).as_posix(),
          'scope_sha256': sha(scope_path), 'counts': {'scope': len(by), 'full_source_reads': len(reviews),
          'full_source_lines': sum(r['source_line_count'] for r in reviews), 'pending': len(pending)},
          'file_reviews': reviews, 'pending_paths': pending, 'claims': claims, 'findings': findings,
          'primary_sources': [{'title': 'Jacob Lurie, Higher Topos Theory', 'url': 'https://www.math.ias.edu/~lurie/papers/HTT.pdf', 'consulted': 'Definition1.1.2.4 and examples1.1.2.5-6, PDF page32: inner-horn extension condition; nearby homotopy-category generators/relations excerpt. Only these defining passages read, not the entire book.', 'accessed_date': '2026-11-10'}],
          'limits': ['Original Rust source/tests read only; no Rust/native/provider execution or original edits.',
                     'Third-party dependencies and referenced sibling test/contract bodies receive no implicit source-reading credit.',
                     'No private benchmark answer access; historical mutation labels are not fresh execution receipts.']}
report['primary_sources'].append({'title':'Bernhard Keller, Introduction to A-infinity algebras and modules',
 'url':'https://webusers.imj-prg.fr/~bernhard.keller/publ/ioan.pdf',
 'consulted':'Sections3.1,3.3,3.4, printed pages5-9: operation/morphism degrees and equations, formality as choice of strict minimal model, and composition formula. Only those defining passages used. The finite F2 countermodel is independently constructed here.',
 'accessed_date':'2026-11-10'})
controls_path=REV/(PREFIX+'_controls.json')
controls=json.loads(controls_path.read_text())
assert controls['status']=='passed' and len(controls['controls'])==13
for control in controls['controls']:
    for pin in control['source_pins']:
        assert sha(ROOT/pin['path'])==pin['sha256']
report['independent_controls']={'path':controls_path.relative_to(ROOT).as_posix(),'sha256':sha(controls_path),'count':len(controls['controls']),
 'limits':'Independent Python mathematics/static branch models, not original Rust execution.'}
ranges = []
for item in claims + findings:
    for evidence in item['source_evidence']:
        assert sha(ROOT / evidence['path']) == evidence['sha256']
        n = len((ROOT / evidence['path']).read_text().splitlines())
        for low, high in evidence['lines']:
            assert 1 <= low <= high <= n
            ranges.append((evidence['path'], low, high))
report_path = REV / (PREFIX + '.json')
report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
text = '# Rust HoTT source audit\n\n' + str(len(reviews)) + ' of24 source/manifests reviewed in full; ' + str(len(pending)) + ' remain pending. This is a source audit, not a native execution or a proof-assistant check.\n\n'
for row in claims + findings:
    text += '**' + row['id'] + '** ' + row['statement'] + '\n\n'
(REV / (PREFIX + '.md')).write_text(text, encoding='utf8')
validation = {'status': 'checkpoint_source_custody_and_ranges_pass', **report['counts'],
              'evidence_ranges': len(ranges), 'report_sha256': sha(report_path),
              'independent_controls':len(controls['controls']),'controls_sha256':sha(controls_path),
              'native_or_provider_runs': 0}
(REV / (PREFIX + '_validation.json')).write_text(json.dumps(validation, indent=2) + '\n', encoding='utf8')
m_path = ROOT / 'dag/swarm_manifest.json'
m = json.loads(m_path.read_text())
if m.get('next_parent_slice', {}).get('scope_manifest') == report['scope_manifest']:
    m['last_completed_parent_slice'] = m['parent_active_slice']
    m['parent_active_slice'] = m.pop('next_parent_slice')
if m['parent_active_slice']['scope_manifest'] == report['scope_manifest']:
    m['parent_active_slice'].update(status=report['status'], full_source_reads=len(reviews), pending=len(pending),controls=len(controls['controls']))
    if not pending and report_path.relative_to(ROOT).as_posix() not in m['completed_followup_slices']:
        m['completed_followup_slices'].append(report_path.relative_to(ROOT).as_posix())
m_path.write_text(json.dumps(m, indent=2) + '\n', encoding='utf8')
print(json.dumps(validation))
