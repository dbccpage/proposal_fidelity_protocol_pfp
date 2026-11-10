"""Manual full-body wiki assessments and explicitly inherited source-audit context."""
import collections,hashlib,json,pathlib,re
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_wiki_tests'
scope=json.loads((H/(P+'_scope.json')).read_text());ledger=json.loads((H/(P+'_read_ledger.json')).read_text())
def sha(path):return hashlib.sha256((R/path).read_bytes()).hexdigest()
def ev(path,ranges):return {'path':path,'sha256':sha(path),'lines':ranges}
def page(name,ranges):return ev('wiki/Test-'+name+'.md',ranges)

# Each entry was written after the entire numbered body was emitted without truncation.
# Fields: page stem, mathematical contribution, assessment/usefulness, explicit limits.
manual=[
('Assignment-Dual-Potentials','Finite assignment weak duality and Hall deficiency.',
 'Useful certificate-first introduction: feasible permutation plus tight dual objective excludes a cheaper assignment; a deficient row neighborhood excludes a perfect matching. It explains Boolean/index/sense hazards and retained case/mutation populations clearly.',
 'The standard-max convention is not implemented correctly at zero optimum (AC55-F01); the replay mutation loop skips the retained envelope key (AC55-F04). Historical pass counts do not certify total input handling, independent checker errors or all advertised bounds.'),
('Calibration-Task-Bank','Exact graph cycle rank, finite rational Hodge decomposition and computed claim classification.',
 'Useful small reviewer calibration design: exact flagged-ID sets, planted unsupported statements, prompt-fragment binding and own-function execution separate answer syntax from claimed truth. It identifies five tasks and port adaptations.',
 'A checker accepting its own reference establishes consistency, not independent truth or reviewer generalization. One-bit feedback reduces diagnostic leakage but does not prove resistance to adaptive oracle probing. No answer-key or --reference invocation was performed; owner implementation remains unaudited here.'),
('Candidate-Revision-Telemetry','AST syntax recognition, diff arithmetic and finite ancestor-selection heuristic.',
 'Accurately limits these tools to telemetry rather than acceptance. Float-literal detection, changed-line/token ratios and consecutive-failure backtracking have concrete test examples and a reproducible entry point.',
 'Syntax acceptance does not establish behavior or exact arithmetic: computed floats, imported operations and effects are outside the stated literal scan. Highest recorded score and five example tests do not prove optimal search, semantic improvement or reliable oracle scores; owners were not rerun.'),
('Certified-Run-Replay-Store','Finite relational storage and deterministic re-evaluation of supplied cases/answers.',
 'Useful description of sample sizes, threaded replay and omitted provider/budget tests. It correctly separates the store from mathematical interpretation and treats checker exceptions as replay failures.',
 'Current re-evaluation is not authenticated historical execution or a frozen checker version. C054/C055 mutation loops silently skip mutated_result records (AC54-F03/AC55-F04), contradicting the page-wide statement that every listed challenge checks a sample. Eleven historical tests were not rerun.'),
('Checkerboard-Paths','Finite combinatorial path counts and rational complex weighted sums.',
 'Clear carrier: integer time/position, unit left/right steps, corners, endpoint and empty-path cases. Fieldwise direction/corner histograms are more informative than a total-only comparator; explicitly no continuum, normalization or unitarity claim.',
 'Declared corner weights are premises, not derived dynamics. Bounded host agreement and selected mutation tests do not prove all parser/algorithm inputs. Historical 112-pass claim and runtime cost at horizon32 were not re-executed; shared hash-custody wording needs an externally retained pin.'),
('Clique-Homology','Finite clique complex and ordinary rational homology by boundary rank.',
 'Useful exact bounded topology example with six vertices, dimensions0..4, orientation signs and explicit truncation/torsion limits. The four-cycle versus filled triangles comparison correctly changes H1 from1 to0.',
 'Equal Betti numbers are only a necessary invariant for an isomorphism claim, not a classifier. Top-degree truncation changes the complex and must stay in the answer. No fresh 111-test replay; raw payload/digest co-storage does not establish historical immutability.'),
('Cochains-Hodge-Adapter','Finite incidence/cochain nilpotency, graph exactness and an admitted diagonal dual map.',
 'Strong distinction between closed and exact: an unfilled triangle supports a closed nonexact unit circulation, while adding its face makes the same cochain nonclosed. Basis orientation and declared positive weights are explicit.',
 'The constructed dual/diagonal map is an adapter, not an inferred smooth Hodge star or geometric theorem. Output correspondence can match a refusal. Runtime and EBNF/contract completeness were not independently audited here; hash statements retain the shared custody caveat.'),
('Commuting-Pauli-Ground-State-Capsule','Finite commuting Hermitian Pauli algebra, exact PSD/kernel witnesses and eigenspace dimension.',
 'Explains genuinely different algebraic and exact spectral predicates and correctly labels optional NumPy work secondary. Positive rational weights, phase tracking, complete minimizing assignments and anticommuting-pair refusals define a useful bounded quantum problem.',
 'Different algorithms do not supply a probability that correlated errors are unlikely; AC2130-F01 finds both accept wrong answer IDs. Exact finite Hamiltonian results are conditional on encoding and do not establish physical model selection. The 365-test expectation is historical, not newly reproduced.'),
('DFA-Minimality-Certificates','Myhill-Nerode accessibility/separation plus independent language equivalence.',
 'Excellent worked certificate: access words prove reachability, pair separators distinguish states, and language equivalence is an additional obligation. The 4-state suffix automaton and 8-state/28-separator example illustrate certificate size.',
 'The sentence that the checker only runs supplied words omits its later-described global language comparison. General-character syntax has shared space/dot defects and the four-letter bound is unenforced (AC56-F01..03). Public runner success is not retained-answer custody (AC56-F04).'),
('Domain-Purity-Scan','Syntactic name matching in a Python AST, not effect analysis.',
 'Useful narrow lint with a positive control and an exact module-classification list. Its stated direct open/read_text/read_bytes/write patterns are concrete and cheap to inspect without importing the package.',
 'The opening claim that domain modules never touch disk is stronger than the scanner: four qualified/aliased I/O forms evade it in WIKIT-P01. It also says nothing about randomness, clocks, environment state, network or transitive callees, so cannot establish referential transparency.'),
('Equational-Proof-Capsule','Equational derivation rules and finite countermodels, conditional on signatures, substitutions and closure.',
 'Pedagogically useful proof/countermodel contrast, term encoding, bounded search and positive/hostile fixtures. A legitimate step-by-step replay can certify equational consequence; a closed finite model satisfying all axioms can refute it.',
 'Current paired acceptance is unsound beyond the fixtures: C050-1 substitutes constants as variables, C050-2 accepts a nonclosed singleton model, C050-3 shows the secondary ignores axioms. The documentation must present these as open verifier defects, not infer soundness from113 tests.'),
('Exact-LP-Dual-Certificates','Rational LP weak duality, Farkas infeasibility and feasible improving rays.',
 'The stated OPTIMAL, INFEASIBLE and UNBOUNDED inequalities are mathematically sufficient for the declared max Ax<=b,x>=0 problem. Canonical number syntax is correctly treated as a separate protocol requirement.',
 'The generic label one correct solver is contradicted by AC51-F01: negative-RHS phase-I can report infeasible on an unbounded feasible problem; judges catch it. Fixture success is not solver completeness. The universal64/48/14 package template is false for other named challenges.'),
('Exact-Linear-System-Witnesses','Rank-nullity via independent kernel columns and a nonzero rank minor; left-null inconsistency witness.',
 'Correct compact certificate argument: rank>=r plus n-r independent kernel vectors forces rank=r and kernel completeness; y^TA=0,y^Tb!=0 refutes solvability. Empty/degenerate inputs and malformed index risks are useful.',
 'AC54-F01 documents accepted malformed fraction1/1/99 and Boolean inputs; AC54-F03 finds replay mutations skipped. Polynomial verification is relative to exact rational bit encoding, not just dimension. Historical45+2 tests are not a universal crash/typing guarantee.'),
('Exact-Matrix-Inversion-Certificates','Determinant/adjugate/inverse identities and nonzero kernel witnesses.',
 'Particularly useful counterexample: scaling det and adj together preserves their identity, so a genuine determinant computation is essential. It explicitly discloses the shared canonical-rational parser, limiting any independence claim.',
 'The determinant lesson is valid even though retained tests pass. AC53-F01/F02 retain null-input and dimension-bound gaps. A canonical grammar is an interface premise; the two copies matching text is not mathematical independence or proof of parser adequacy.'),
('Face-Activation','A finite typed transition on an admitted cell complex and assigned observables.',
 'Keeps a revision increment, exactly one activity-bit change, payload preservation and optional rational mass/drag assignment separate. Correctly states that matching a refusal does not execute a transition or derive observables from topology.',
 'The phrase byte-for-byte payload preservation should mean the declared typed/canonical structure unless raw-byte equality is separately checked. No physical mass/drag law is demonstrated. The 89-test historical result and implementation totality were not rerun.'),
('Finite-Provenance','Finite event ordering, record identity and observation-table consistency.',
 'Useful provenance model: supply before admission, current designation, prior-prefix binding, and unique receipt IDs. It explicitly distinguishes equal inscriptions from equal observations and a permitted successor from an inevitable one.',
 'All relations, observations and interpretations are supplied premises. It establishes neither real history nor issuer identity, exactly as the page notes. Global termination and interpretation validity do not follow from local quiescence; shared raw-hash wording still overstates historical custody.'),
('Finite-Quotients','Factorization through a finite quotient iff a function is constant on each fiber.',
 'States a valid information-loss obstruction and uses explicit conflicting pairs. Candidate operations/observers/costs are supplied, and new distinctions are correctly described as extensions rather than recovering erased information.',
 'Optimality/survival is relative to the enumerated operation family, selected demands and chosen costs. Equal payloads can still be distinguished by admitted identity-sensitive operations. No universal creative search or observer adequacy is established; runtime tests were not rerun.'),
('Grammar-Profiles','Whole-input recognition in four named finite syntax profiles.',
 'Useful strict syntax/semantics boundary: no trimming, byte repair or aliasing, explicit raw-byte digest, and an EBNF reference compared on shared conformance cases. Syntax acceptance expressly does not establish truth.',
 'Agreement on conformance cases is not a proof of equivalence for every grammar word. Hashes need preserved expected values for later custody. No new recognizer run or complete grammar-theoretic proof was performed; historical117-test result remains a claim.'),
('Graph-Coboundary-Repair-Capsule','Weighted finite L1 projection onto graph coboundaries with a dual circulation.',
 'The primal/dual equality argument is sound for positive weights: dual conservation/capacity lower-bounds any repair, and matching values attain the bound. Zero objective then means exact coboundary; gauge and cycle controls are appropriate.',
 'AC1120-F06 shows refusal witness and input-domain failures despite the stated canonical protocol. Positive certificate mathematics does not validate every refusal or encoding. The prior recreated-receipts46-witness controls are historical-source arithmetic, not a new run of this wiki command.'),
('Hodge-Decomposition','Exact orthogonal decomposition for a declared finite rational inner product and chain complex.',
 'Clearly separates exact, coexact and harmonic components, boundary/Laplacian calculation and a separately named complement-face operation. Typed full-answer comparison and explicit continuum refusal are useful scope controls.',
 'The finite metric/inner product and simplicial encoding are premises; uniqueness of projected components does not make a reported basis canonical without its convention. No smooth or physical Hodge law follows. Historical155 tests and source behavior were not replayed.'),
('Integer-Obstruction-Lift','Integral cokernel/torsion versus rational scalar extension, and parity lower bounds.',
 'Correctly warns that solving 2c=1 overQ does not repair the integer problem. In the declared three-term complex H1=Z/2, rational H1=0 while H0=Q; odd parity gives global residual minimum1 at0,1. Fresh small controls confirm the scalar claims.',
 'The chain maps and degree indexing must remain declared; multiplication by2 alone does not specify every homology group. Rational acyclicity is expressly denied. No applied repair, authorized carrier change or general integral solver follows from the worksheet.'),
('Interference-Weights','Exact admitted two-state Hadamard arithmetic and noninjective probability readout.',
 'Correct example: equal computational-basis probabilities can hide opposite relative phases and lead to different later probabilities. Global phase invariance and the square-root-lift convention are separated from phase reconstruction.',
 'Born readout and Hadamard action are explicit assumptions, not derived physical laws or observations. Exact symbolic/rational representations do not imply all amplitudes are rational. No quantum-computer experiment or new provider run; historical64 tests remain bounded.'),
('LP-Certificates','Finite two-variable primal/dual feasibility and optimality, distinct from uniqueness.',
 'Clear weak-duality teaching example: equal objectives are insufficient without feasibility, and a second distinct optimal point disproves uniqueness. The improvement trace is explicitly supplied and checked, not generated by an optimizer.',
 'One certificate leaves uniqueness unestablished; certificate checking is not a complete LP solver. Exact arithmetic is relative to the admitted input grammar. Historical136 tests and trace/custody operations were not rerun.'),
('Lattice-Gauge-Gauss-Law-Capsule','Finite Z2 chain/cochain ranks, symplectic logical operators and charge sectors.',
 'Useful explanation of why 2g fails for nonorientable surfaces and of two finite algebraic verification routes. The model, cell complex and sector semantics are supplied physical/mathematical premises.',
 'AC39-F01/F02 show charge-map and early-return domain gaps: paired judges can accept missing or extraneous charges and a sector result without any graph. Thus the categorical statement that non-manifold inputs are refused needs qualification. No physical-model derivation or new76-test run.'),
('Max-Flow-Min-Cut-Certificates','Integer feasible flow/cut equality as a finite optimality certificate.',
 'Correct certificate reasoning: conservation/capacities bound flow by every source/sink cut; an equal cut attains that bound. The page usefully discloses that replay samples only five mutations and lacks a package test directory.',
 'AC52-F01..03 show float/bool coercion and undeclared boundary gaps, plus recursion failure on a long chain. Exact integers above machine range are mathematically valid but can exceed TASK bounds. Two replay tests are not all48-mutant coverage or solver completeness.'),
('Normalization-Readout','Exact normalization, symbolic square-root lifting and nonuniqueness of representations.',
 'Strong scope statement: squaring chosen radicals recovers normalized weights by construction, not experimental evidence for Born probabilities. It binds radicands to original weights and distinguishes ordinary sum from squared norm.',
 'A physical readout interpretation and representation selection require additional premises. Reproducing a vector through two admitted maps does not make either unique. Historical72 tests, strict decoder behavior and raw custody were not rerun.'),
('Oracle-Fixture-Freeze','Finite interpreter observations, scalar-wide fingerprints and seeded binary64 samples.',
 'Useful oracle-version pinning and deterministic artifact generation, with Unicode15.0 refusal explicitly described. It distinguishes whole scalar scans from a finite float stream in its inventory.',
 'The JSON payload actually marks freeze=after-native-implementation, so the asserted pre-port chronology is unsupported. Full LCG classification finds129NaNs/130subnormals but no infinity or signed zero; separate explicit vectors must not be attributed to the sample. Fingerprints do not prove universal string/context or float equivalence.'),
('Paper-Run-Role-Gated-Transitions','Finite role/event policy validation and claim-to-obligation tables.',
 'Useful separation of planner metadata, obligation creation and authorizer decisions. It documents dev-only omissions and trimmed adapters rather than presenting every planned stage as executed.',
 'TransitionEvent contains a caller-supplied role enum, not a signature or authentication field. The opening signed-with-a-role wording should say role-labelled. Mapping a claim to a Lean obligation is not a Lean proof;17 examples are not exhaustive testing of arbitrary payloads or runtime identities.'),
('Provider-Byte-Ceilings','Bounded UTF-8 byte accounting and raw-response admission predicates.',
 'Good boundary tests for combined prompts, octet-sized memoryviews, multibyte characters, size-before-decode ordering, unpaired surrogates and text-free refusal records. It explicitly discloses omitted gateway/budget integration.',
 'An observed_bytes counter alone does not prove runtime work bounds; that needs source/control evidence. Already materialized buffers and transport-level allocation are outside these direct checks. No inference of no-charge/no-dispatch behavior survives the removed gateway tests; owners were not replayed here.'),
('Qa-Receipt-Invariants','Typed finite evidence records, value invariants and canonical content integrity.',
 'Useful invariant/break/witness organization distinguishes mutation statuses, exact Boolean/integer types, audit veto and empty digest behavior. It explains that only three declared mutation outcomes enter the denominator.',
 'Receipt consistency does not authenticate tests or validate examiner classifications. MUTATION comments describe hypothetical edits, not proof that a mutation campaign ran. A minimum sufficient set of all needed safeguards is not established by13 tests; no new suite run.'),
('Quadratic-Form-Local-Obstructions','Exact isotropic-point substitution and local Hilbert-symbol obstruction under appropriate nondegenerate assumptions.',
 'Useful asymmetric yes/no witnesses and the product-formula paired-obstruction example. For rational nondegenerate ternary forms, a valid local obstruction excludes global isotropy; zero coefficients need a separate elementary branch.',
 'The page overstates implemented Legendre search and cheap arbitrary-size places: AC48-F01/F02 document incomplete point search, a primary pseudoprime escape and unbounded secondary trial division. Fixed-corpus pass counts do not discharge primality, runtime or complete solving obligations.'),
('Recurrence-Absence-Certificates','Finite homogeneous coefficient equations and a full-rank minor obstruction.',
 'A nonsingular coefficient minor can exclude a nonzero bounded-order/degree recurrence on those indices, provided all candidate start positions are bound to the case. This is a useful finite certificate contrasted with unsuccessful search.',
 'Finite prefix plus held-out substitution cannot establish an all-n law; WIKIT-P03 gives two indistinguishable observed prefixes with different continuations. AC47-F01/F02 additionally show answer-controlled starts/ranges that invalidate the advertised case-wide inference. Root testing and public-runner limits also remain.'),
('Rewrite-Normal-Form-Loss','Terminating finite string rewriting and failure of query factorization through normal forms.',
 'Correctly displays the unjoined critical peak abc→dc/ae, a separately extended presentation joining this peak, and lost letter-a count. Strict shortening proves termination; retaining original bytes makes the pair trivially reversible.',
 'One joined peak is not global confluence, which the page expressly disclaims. --max-states bounds exploration rather than proving absence beyond the visited set. Raw-original retention and its hash need a stable external receipt for historical custody; no new76-test run.'),
('Role-Submission-Comparison','Literal finite record comparison plus a separate bounded integer-sum predicate.',
 'Strong limit: Red/Green agreement is not truth; opaque propositions stay unverified, integer-sum outcomes can be checked, and no action authority is minted. Preserving disagreements and task digests is useful for review traceability.',
 'Only the declared finite predicate is executable semantics. Labels, roles and consensus do not authenticate reviewers or validate arbitrary prose. A task digest must be externally bound to prevent co-replacement; no general research judgment or new121-test run.'),
('SQL-Null-Safe-Query-Synthesis','Finite bag-valued relational evaluation with three-valued predicates.',
 'Useful separation of proposer imports, read-only SQLite execution, exact column headings and row multiplicity. It clearly describes two reference evaluators and supplied hidden-database testing rather than a formal relational-equivalence algorithm.',
 'C059-F01 proves finite-suite overfit; C059-F02 finds unenforced construct/ledger requirements, and F03 identifies dialect/coercion disagreement. Imported-oracle separation is not semantic completeness. Generic one-correct-solver language is contradicted by F04. No query or private database was executed here.'),
('Singular-Integrals','Exact log expressions and distinct improper, principal-value and paired-cutoff limits.',
 'Correct mathematics for nonzero c and a<b: exterior pole gives c log(|b-p|/|a-p|); interior one-sided divergence does not cancel into an improper integral, while a declared symmetric cutoff gives c log(R/L). Different fixed cutoff ratios encode different procedures.',
 'A symbolic log expression is exact without being rational, and route replay is consistency of supplied teaching states, not a proof of every analysis theorem. Endpoint cases need their own divergence branch. Tests may write default outputs; none were run in this audit.'),
('Sorting-Network-Zero-One-Principle','Exhaustive finite Boolean evaluation and its threshold-lifting proof for total-order comparators.',
 'Explains a legitimate complete certificate at n<=12 and distinct infeasibility grounds. Crucially discloses the external optimal-size table, leaked historical prompt bounds and generator/opaque-name mismatch.',
 'The zero-one theorem presumes correct comparator/interpreter semantics; it does not prove minimality without an admitted lower bound. AC57-F01 finds the public runner skips prefix/forbidden constraints and accepts arbitrary non-SOLVED status. The literature table was not externally reverified or treated as newly proved.'),
('Stage-Receipt-Tape','Append behavior and finite role/rebuild guards on caller-supplied receipt events.',
 'Good explicit evidence ceiling: tape is not authenticated or tamper-evident and does not prove a stage ran. Byte-preserving append, failure propagation and checks-before-write are useful bounded operational properties.',
 'Single-process tests do not establish concurrent atomicity, crash/power-loss durability or cryptographic integrity. Rebuild compliance depends on truthful caller fields and intact existing history. No new14-test run or production tape mutation was performed.'),
('Strict-Provider-Reply-JSON','Strict lexical JSON admission: duplicates, nonfinite numbers, root type and raw-byte bounds.',
 'Useful positive/negative controls and fixed-message refusal without echoing hostile text. It discloses that provider parser call-order assertions were removed with the gateway.',
 'One unambiguous JSON value is not one complete semantic interpretation: schema, Unicode scalar validity, meaning, depth/resource limits and downstream arithmetic remain separate obligations. No current gateway/budget behavior or all-input totality is proved by30 fixtures; no provider invoked.'),
('Superoptimizer-Equivalence-Limits','Finite bit-vector program semantics, exhaustive small-width equivalence versus fixed sampled agreement.',
 'The page makes the main evidence boundary unusually visible:8-bit complete domains versus wider chosen inputs, plus a concrete failed OR-for-XOR replacement. It also distinguishes shorter-program acceptance from proof of minimality and admits sampling gaps.',
 'Calling fixed public samples strong evidence requires an error/adversary model; C058-F01 already constructs a rare-trigger false equivalence. Reference UNKNOWN and runner exit behavior have separate defects. SAT/SMT would certify equivalence only with faithful encoding and a trusted/proof-checked solver, not automatically every claim.'),
('Tautological-Assertion-Lint','Finite AST-pattern detection of assertions disconnected from the intended subject.',
 'Useful deliberately narrow preflight: constant assertions, literal comparisons and self-raised exceptions are concrete suspicious patterns. Positive and negative snippets support pattern behavior rather than broad test quality.',
 'A constant False assertion is not a logical tautology; the category is better described as input-independent assertion. A pattern hit/miss does not decide semantic usefulness, and runtime-looking assertions can still be vacuous. Four examples and comments are not a mutation campaign.'),
('Template-Substitution','Single-pass substitution versus reprocessing inserted text.',
 'Correct primary example: data containing ${question} is changed by a data-first then question replacement, while string.Template substitutes once. It explicitly denies prompt-injection prevention and discloses unported mutation orchestration.',
 'The second exercise at line46 is wrong for the specified replacement order: ${data} inside the question is inserted after the data pass and is preserved by both methods. WIKIT-P05 reproduces this; reverse the order to exhibit the converse problem. No model-security claim follows from byte preservation.'),
('Trace-Replay-Refusal','Regular trace syntax, typed-state equality and finite task-bound transition replay.',
 'Clearly separates shape checks, stationarity, missing-state unverified status and step-by-step task semantics. Explicit task binding prevents a proposal from silently selecting a different problem; no authority to act is conferred.',
 'Legal event labels alone do not prove execution or semantic state correctness. The historical87-test claim is qualified by an explicitly skipped fixture-dependent test; no full runtime replay was attempted. Bounded grammar/replay evidence is not a general process or authority proof.'),
('Triangle-Angle-Defects','Exact triangle-existence discriminant and formal local angular deficits.',
 'For positive squared sides, H=4xy-(x+y-z)^2>0 is equivalent to strict triangle inequalities and area squared isH/16. Complete incidence and lengths are required; unresolved arccos sums remain symbolic rather than false numerical closure.',
 'Local metric/angle consistency does not establish a global manifold, embedding or physical curvature interpretation. The H=0 example is independently confirmed. Historical122 tests and implementation neighborhood classification were not rerun.'),
('Triangle-Fan-Pairing','Finite equilateral intrinsic-fan geometry and a separate signed-pairing carrier.',
 'Correct finite counts: V=n+1,E=2n,F=n giveχ=1; unit triangle center angle is1/6 turn and deficit1-n/6. The connected-cycle link assumption is explicit, and independent pairing data is not identified with geometry.',
 'An intrinsic fan need not embed flatly in the Euclidean plane when deficit is nonzero. Signed pair cancellation needs the stated weight/sign relation, not just a label. Exact deficits5/6/7 are independently confirmed, without running the128-test suite.'),
('Xor-Cycle-Obstruction','Finite F2 cycle parity, exhaustive assignments and complete unit-cost repair enumeration.',
 'A crisp complete small example: XORing all three edge equations cancels variables and contradicts odd RHS parity; all eight assignments and all three single-edge repairs can be enumerated. Fresh controls reproduce these counts and distinguish complete repair sets from one witness.',
 'The carrier is exactly three vertices, binary values and the declared costs, not all local/global consistency problems. Booleans and malformed bytes require separate enforcement. The Python3.14 recursion change is a historical port note, not newly reproduced behavior.'),
('Yardstick-Arm-Statistics','Wilson intervals, paired exact McNemar arithmetic, Pareto ordering and heuristic allocation.',
 'Useful operational metrics keep checker-accepted results distinct from self-grading, pair repeated trials one-to-one, and use None for no-success cost. Literal finding deduplication and promotion/retirement thresholds are described concretely.',
 'Checker acceptance is not independently established truth or detector adequacy. Wilson/McNemar interpretations require an appropriate sampling/pairing model; adaptive dependent tasks and repeated model trials need care. Point-threshold promotion and fixed-seed Thompson tests do not prove statistical improvement, causal seat value or general learning effectiveness.')]
assert len(manual)==len(ledger)==47

# Explicit cross-references to previously completed source audits, not new runtime results.
refs={
0:('additional_challenges_051_059.json',['AC55-F01','AC55-F02','AC55-F03','AC55-F04']),
3:('additional_challenges_051_059.json',['AC54-F03','AC55-F04']),
7:('additional_challenges_021_030.json',['AC2130-F01']),
8:('additional_challenges_051_059.json',['AC56-F01','AC56-F02','AC56-F03','AC56-F04']),
10:('additional_challenges_041_050.json',['C050-1','C050-2','C050-3','C050-4']),
11:('additional_challenges_051_059.json',['AC51-F01','AC51-F02']),
12:('additional_challenges_051_059.json',['AC54-F01','AC54-F02','AC54-F03','AC54-F04']),
13:('additional_challenges_051_059.json',['AC53-F01','AC53-F02']),
18:('additional_challenges_011_020.json',['AC1120-F06']),
23:('additional_challenges_031_040.json',['AC39-F01','AC39-F02']),
24:('additional_challenges_051_059.json',['AC52-F01','AC52-F02','AC52-F03']),
30:('additional_challenges_041_050.json',['AC48-F01','AC48-F02','AC48-F03','AC48-F04']),
31:('additional_challenges_041_050.json',['AC47-F01','AC47-F02','AC47-F03','AC47-F04']),
34:('additional_challenges_051_059.json',['C059-F01','C059-F02','C059-F03','C059-F04','C059-F05','C059-F06']),
36:('additional_challenges_051_059.json',['AC57-F01','AC57-F02','AC57-F03','AC57-F04']),
39:('additional_challenges_051_059.json',['C058-F01','C058-F02','C058-F03','C058-F04','C058-F05','C058-F06'])}
prior={};pins={};file_reviews=[];context=[]
for i,(stem,math,assessment,limits)in enumerate(manual):
 row=ledger[i];path='wiki/Test-'+stem+'.md';assert path==row['path']and row['body_emitted']
 assert sha(path)==row['sha256']
 comparison=[]
 if i in refs:
  name,ids=refs[i]
  if name not in prior:prior[name]=json.loads((H/name).read_text())
  for fid in ids:
   finding=next(f for f in prior[name]['findings']if f['id']==fid)
   selected=[]
   for item in finding.get('evidence',[]):
    sp=item.get('path','')
    if sp.startswith('workflows/')and item.get('sha256'):
     assert sha(sp)==item['sha256'],sp
     pins[sp]=item['sha256'];selected.append({'path':sp,'sha256':item['sha256']})
   comparison.append({'report':'dag/reviews/'+name,'report_sha256':sha('dag/reviews/'+name),
                      'finding_id':fid,'finding':finding.get('claim',finding.get('finding',finding.get('statement'))),
                      'source_pins_revalidated':selected,
                      'basis':'Previously completed dedicated source review and its bounded controls; not a new runtime replay or full source-reading transfer.'})
 file_reviews.append({'path':path,'sha256':row['sha256'],'bytes':row['bytes'],'full_source_read':True,
                      'reviewed_lines':[[1,row['lines']]],'review_level':'full_body_mathematical_and_usefulness_review',
                      'mathematical_contribution':math,'assessment':assessment,'limitations':[limits],
                      'source_review_comparisons':comparison,
                      'runtime_validation':'No wiki command or underlying full suite executed in this slice.'})

def inherited(index):return file_reviews[index]['source_review_comparisons']
findings=[
 {'id':'WIKIT-F001','severity':'high','finding':'Equational capsule documentation presents paired certificate acceptance without the known soundness defects.',
  'evidence':[page('Equational-Proof-Capsule',[[3,21],[27,41]])],'prior_source_evidence':inherited(10),
  'reason':'Both checkers accept c=d from ground axiom a=b by substituting constants; both accept a claimed singleton operation table leaving its carrier. The second countermodel route also ignores axioms. These directly defeat the advertised certificate semantics outside the retained fixture set.',
  'action':'Add a visible current soundness limitation and link the concrete source findings; keep113 historical test passes distinct from proof of validity. No source repair made.'},
 {'id':'WIKIT-F002','severity':'high','finding':'The recurrence page conflates finite observed agreement with an all-n law and omits the accepted start-range narrowing defect.',
  'evidence':[page('Recurrence-Absence-Certificates',[[3,15],[53,59]])],'prior_source_evidence':inherited(31),'probe':'WIKIT-P03',
  'reason':'Finite prefix/held-out samples do not determine an infinite continuation. A nonsingular minor only excludes coefficients on its actual indices and admitted start range; AC47-F02 shows the answer can narrow that range and obtain an accepted false case-wide absence.',
  'action':'Describe fitted/held-out-valid recurrences separately from globally proved laws. Bind absence/start domains to the case, and link the unresolved checker findings.'},
 {'id':'WIKIT-F003','severity':'medium','finding':'The replay-store page says every listed challenge tests hostile samples, but C054/C055 silently skip the retained mutation envelopes.',
  'evidence':[page('Certified-Run-Replay-Store',[[12,25],[32,45],[68,72]])],'prior_source_evidence':inherited(3),
  'reason':'The prior source audit found loops read corrupted_result or candidate while files use mutated_result. A passing replay suite therefore provides no mutation rejection evidence for those loops.',
  'action':'Qualify the documented coverage and preserve the source repair backlog; sampling counts should report actually evaluated mutations, not selected filenames.'},
 {'id':'WIKIT-F004','severity':'medium','finding':'Oracle-freeze chronology and binary64 sample coverage are overstated.',
  'evidence':[page('Oracle-Fixture-Freeze',[[3,8],[21,24],[39,42]]),ev('workflows/tasks/oracle_fixture_freeze/freeze_json_acceptance.py',[[29,56]])],
  'probe':'WIKIT-P02','reason':'The emitted JSON explicitly marks freeze=after-native-implementation. Its262144 seeded values contain261885 normals,130subnormals and129NaNs, but no infinity or signed zero. Infinity is covered by separate literal vectors; -0.0 truthiness is a different check. Neither proves pre-implementation custody.',
  'action':'Describe actual freeze timing, separate exhaustive scalar scans, random-bit samples and explicit special vectors, and retain a separately authenticated pre-port artifact if chronology is important.'},
 {'id':'WIKIT-F005','severity':'medium','finding':'The domain-purity page promotes a direct AST name scan to a guarantee of no disk I/O.',
  'evidence':[page('Domain-Purity-Scan',[[3,7],[24,31],[59,63]]),ev('workflows/tasks/paper_run_rules/test_paper_run_domain_purity.py',[[44,55]])],
  'probe':'WIKIT-P01','reason':'The actual scanner detects direct open but misses aliasing, Path.open, os.open and io.open imported under another name. It does not analyze transitive effects or other nondeterministic inputs.',
  'action':'Call it a bounded syntactic lint, enumerate unsupported effect paths, and avoid inferring purity or replay determinism from an empty scan.'},
 {'id':'WIKIT-F006','severity':'medium','finding':'Repeated receipt boilerplate overstates what a co-stored hash establishes about history.',
  'evidence':[page('Checkerboard-Paths',[[40,42]]),page('Finite-Provenance',[[40,42]]),page('Xor-Cycle-Obstruction',[[41,43]])],
  'probe':'WIKIT-P04','reason':'A digest shows current bytes agree with an expected digest. If data and its co-stored receipt are both rewritten, local consistency survives; the digest alone does not show unchanged bytes since a past run. The existing authorship disclaimer is helpful but does not supply an external time/identity anchor.',
  'action':'State the protected expected-digest assumption and distinguish fresh artifact consistency, immutable archive custody and authenticated execution. Keep the existing explicit no-authorship limit.'},
 {'id':'WIKIT-F007','severity':'low','finding':'The universal challenge-package template gives false counts and overstates reference solver correctness.',
  'evidence':[page('Exact-LP-Dual-Certificates',[[23,36]]),page('Graph-Coboundary-Repair-Capsule',[[38,45]]),page('Commuting-Pauli-Ground-State-Capsule',[[35,43]])],
  'prior_source_evidence':inherited(11),'reason':'Pages say every challenge has14 examples,64 judge cases and48 mutations, while these same wiki pages enumerate46 graph cases/40 mutations and44 Pauli cases/51 mutations. Calling reference_solver one correct solver is also contradicted by the phase-I LP control, which judges correctly reject.',
  'action':'Scope the layout/count paragraph to the particular family and use reference implementation rather than a correctness guarantee.'},
 {'id':'WIKIT-F008','severity':'medium','finding':'Different Pauli checker algorithms are described as making shared errors unlikely without an error model.',
  'evidence':[page('Commuting-Pauli-Ground-State-Capsule',[[15,23]])],'prior_source_evidence':inherited(7),
  'reason':'Algebraic/spectral diversity is valuable but supplies no quantitative independence probability. Both routes accept a wrong output ID in the dedicated source audit; shared framing, specifications and assumptions can correlate failures even when energy algorithms differ.',
  'action':'Describe algorithmic diversity and its tested limits, without probabilistic assurance or multiplying confidence. Preserve the exact finite energy argument separately.'},
 {'id':'WIKIT-F009','severity':'medium','finding':'The quadratic-form page describes a complete Legendre-style producer and uniformly small obstruction check beyond what the implementation establishes.',
  'evidence':[page('Quadratic-Form-Local-Obstructions',[[3,8],[58,65]])],'prior_source_evidence':inherited(30),
  'reason':'The dedicated audit has a simple valid point skipped by bounded search, a composite accepted by the primary large-integer primality path and a secondary trial-division check without a resource bound. Hilbert-symbol arithmetic does not discharge primality or solver completeness by itself.',
  'action':'Separate the theorem-level certificate from implemented primality/search limits; avoid promising one small computation independent of certificate size or complete Legendre descent.'},
 {'id':'WIKIT-F010','severity':'low','finding':'Role-labelled paper transitions are called signed even though the value object has no authentication material.',
  'evidence':[page('Paper-Run-Role-Gated-Transitions',[[3,8],[38,43]]),ev('workflows/tasks/paper_run_rules/paperrun/transition_event.py',[[16,28]]),page('Stage-Receipt-Tape',[[33,38]])],
  'reason':'The event supplies a role enum and hashes/flags, not a cryptographic signature or authenticated principal. The separate stage-tape page correctly disclaims authentication.',
  'action':'Use role-labelled, and distinguish policy validation from determining who actually submitted the event.'},
 {'id':'WIKIT-F011','severity':'low','finding':'The template page\'s converse exercise does not differ under its stated replacement order.',
  'evidence':[page('Template-Substitution',[[7,7],[44,46]])],'probe':'WIKIT-P05',
  'reason':'With data replaced first, ${data} inside a subsequently inserted question is not revisited; both single-pass and sequential renderings preserve it.',
  'action':'Explicitly reverse the replacement order for the converse example; retain the correct primary data-containing-question example.'},
]

claims=[
 {'id':'WIKIT-C01','claim':'All47 assigned pages were fully read and assessed for mathematical content, utility and evidence limits; no underlying suite pass count is newly asserted.',
  'evidence':[{'artifact':P+'_read_ledger.json','scope_files':47}],'dependencies':['Exact8050 frozen hashes and complete line emissions.'],'limitations':['This documentation slice is not a semantic review of all linked owners.']},
 {'id':'WIKIT-C02','claim':'The LP, assignment, flow and linear-algebra pages describe useful finite certificates whose mathematical force comes from explicit feasibility, duality, rank or annihilator conditions.',
  'evidence':[page('Exact-LP-Dual-Certificates',[[7,19]]),page('Exact-Linear-System-Witnesses',[[7,17]]),page('Max-Flow-Min-Cut-Certificates',[[7,18]])],
  'dependencies':['Exact arithmetic, admitted carrier/shape/encoding, positive or nonnegative constraints as stated.'],'limitations':['The existence of a sound mathematical argument does not establish enforcement by every current checker; source gaps are cross-referenced.']},
 {'id':'WIKIT-C03','claim':'Exhaustive bounded enumeration can discharge a finite proposition, while finite sample agreement alone cannot establish arbitrary SQL equivalence, wide bit-vector equivalence or an infinite recurrence law.',
  'evidence':[page('Sorting-Network-Zero-One-Principle',[[3,7]]),page('Superoptimizer-Equivalence-Limits',[[23,30]]),page('Recurrence-Absence-Certificates',[[7,15]])],
  'dependencies':['Correct interpreter and complete admitted finite domain for exhaustive cases; supplied samples for the others.'],'limitations':['Zero-one lifting uses the comparator threshold property. Statistical strength requires a sampling/error model and does not follow from fixed public samples.']},
 {'id':'WIKIT-C04','claim':'Several teaching pages explicitly preserve carrier and physical-premise boundaries: rational lifting does not repair an integer problem, and normalization or phase arithmetic does not derive Born measurement.',
  'evidence':[page('Integer-Obstruction-Lift',[[7,20]]),page('Interference-Weights',[[7,18],[38,38]]),page('Normalization-Readout',[[3,19]])],
  'dependencies':['Declared chain maps, number systems, readout maps and Hadamard operator.'],'limitations':['Exact calculations within these models are not experiments or model-selection arguments.']},
 {'id':'WIKIT-C05','claim':'The quotient, rewrite and provenance pages provide useful finite countermodels to lossless normalization, consensus-as-truth and inferred history.',
  'evidence':[page('Finite-Quotients',[[3,19]]),page('Rewrite-Normal-Form-Loss',[[7,19],[54,54]]),page('Role-Submission-Comparison',[[7,20]])],
  'dependencies':['Supplied finite maps, operation family, rewrite rules and host predicate.'],'limitations':['No universal observer adequacy, global confluence from one joined peak, real history authentication or arbitrary prose verification.']},
 {'id':'WIKIT-C06','claim':'Raw-byte guards, syntax checks, typed receipts and role gates contribute distinct protocol predicates; they are not by themselves mathematical proof or authenticated execution.',
  'evidence':[page('Strict-Provider-Reply-JSON',[[12,29],[70,76]]),page('Stage-Receipt-Tape',[[33,38]]),page('Domain-Purity-Scan',[[3,7],[59,63]])],
  'dependencies':['Actually enforced field/byte/shape predicates and preserved caller binding.'],'limitations':['No current gateway/provider/budget integration replay; source purity/authentication gaps are explicit.']},
 {'id':'WIKIT-C07','claim':'Detector mutation tests and checker-accepted yield are operational evidence relative to selected attacks and validators, not universal detector adequacy or independently true model accuracy.',
  'evidence':[page('Yardstick-Arm-Statistics',[[3,18],[24,48]]),page('Qa-Receipt-Invariants',[[25,43]])],
  'dependencies':['Valid paired sampling, trustworthy ground labels and actually exercised mutation records.'],'limitations':['Wilson/McNemar/Thompson numerical examples do not establish inferential assumptions, causal credit or statistical significance of a promotion.']},
 {'id':'WIKIT-C08','claim':'Six fresh bounded controls confirm four scanner blind spots, the exact seeded float population, a finite-prefix countermodel, the need for a retained hash anchor, template-order behavior and selected finite worksheet arithmetic.',
  'evidence':[{'artifact':P+'_probes.json'}],'dependencies':['Reviewed scanner-function AST only; otherwise independent standard-library integer/Fraction calculations.'],'limitations':['No historical command, private answer key, provider, native build or broad owner test suite was executed.']},
]

support=[]
for path,assessment in [
 ('workflows/tasks/paper_run_rules/test_paper_run_domain_purity.py','Complete scanner/test body read. Direct syntactic call-name matching with explicit module lists and positive control; extracted only disk_io_calls for synthetic parsing. Four alias/qualified blind spots reproduced; this is not a whole-package effect audit.'),
 ('workflows/tasks/oracle_fixture_freeze/freeze_json_acceptance.py','Full freezer body read. Seed/count/LCG are explicit; separate RAWS truthiness and literal special floats are not stream members. build_payload marks after-native-implementation. Only independent bit classification executed, not fixture writer.'),
 ('workflows/tasks/paper_run_rules/paperrun/transition_event.py','Full33-line immutable Pydantic event body read. Role enum, event string, hashes and Boolean claims have no signature/authenticator field; no gate or identity-runtime execution performed.')]:
 support.append({'path':path,'sha256':sha(path),'full_source_read':True,'reviewed_lines':[[1,len((R/path).read_text().splitlines())]],'assessment':assessment})

hash_pages=[]
for r in file_reviews:
 if 'A hash shows that bytes were not changed after the run' in (R/r['path']).read_text():hash_pages.append(r['path'])
report={'source_commit':scope['source_commit'],'status':'complete_scoped_full_body_review','scope':{'files':47,'bytes':sum(r['bytes']for r in file_reviews),'full_source_read':47,'pending':0},
 'claims':claims,'findings':findings,'file_reviews':file_reviews,'supporting_source_reads':support,
 'prior_source_pin_validation':{'paths':len(pins),'pins':pins,'basis':'Exact current source hashes match the consulted prior evidence; prior findings are attributed, not rerun.'},
 'repeated_hash_custody_wording':hash_pages,
 'validation':[{'artifact':P+'_probes.json','result':'Six bounded controls passed while reproducing documented counterexamples.'},
               {'artifact':P+'_validation.json','result':'See independent final scope/hash/range/schema validation.'}],
 'parent_finding_cross_check':{'report':'dag/reviews/additional_wiki_remaining.json','findings':['WIKI-F007','WIKI-F008','WIKI-F009'],
  'helper':'dag/reviews/additional_wiki_math_checks.py','assessment':'No overstatement found within explicit exact additive-carrier limits. D=dtheta-A is joint-gauge invariant; both support1 and support3 repairs attain L1 lower bound2. Missing dialect preservation is appropriately a documentation limitation, not asserted irreversible historical loss.',
  'no_new_parent_scope_credit':True},
 'remaining_work':[],'limits':['All47 page bodies were read; linked code owners are not thereby fully reviewed.',
 'Historical expected test counts and timings are preserved as documentation claims, not new runs.',
 'No original edit, provider/private benchmark/answer-key access, downloads, native build or foreign-repository mutation.']}
(H/(P+'.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
(H/(P+'_notes.json')).write_text(json.dumps({r['path']:{k:r[k]for k in ['mathematical_contribution','assessment','limitations']}for r in file_reviews},indent=2)+'\n',encoding='utf-8')
md='''# Wiki test-page review

All **47 frozen pages (197,686 bytes)** were read in full and assessed. Their strongest contribution is explaining finite certificates, carrier boundaries, exact encodings and the difference between a matched refusal and a solved problem. Existing source-review findings are explicitly attributed; historical test counts were not rerun.

The main corrections needed are:

- **Equational and recurrence certification:** current C050 checkers admit false proofs/nonmodels; finite sequence agreement does not prove an infinite law, and C047 start-range binding is defective.
- **Replay coverage:** C054/C055 custody tests skip their retained mutation envelope field, so passing those tests does not establish the advertised mutation checks.
- **Oracle evidence:** the JSON freezer says it was frozen after native implementation. Its seeded stream contains 129 NaNs and 130 subnormals, but no infinities or signed zero; explicit special cases are separate evidence.
- **Boundary claims:** the purity scanner misses four I/O spellings; co-stored hashes need a retained external expectation to establish historical drift; role labels are not signatures; algorithmic diversity supplies no statistical independence guarantee.
- **Documentation accuracy:** the universal 14/64/48 package template is false, the quadratic-form solver/check cost is overstated, and the template page's converse exercise needs reversed replacement order.

Six bounded controls passed, reproducing the stated counterexamples and selected exact worksheet arithmetic. The JSON records **11 actionable documentation findings**, each page's mathematical contribution/usefulness/limits, three narrowly inspected source owners, and exact prior-source pins. No original sources changed; no provider, private benchmark, answer key or native build was used.
'''
(H/(P+'.md')).write_text(md,encoding='utf-8')
print(json.dumps({'files':len(file_reviews),'findings':len(findings),'claims':len(claims),'prior_owner_pins':len(pins),'hash_wording_pages':len(hash_pages)}))
