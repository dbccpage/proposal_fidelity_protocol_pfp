"""Build evidence-scoped recommendations. Does not modify imported material."""
import ast
import collections
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BASE = 'pilots/anomalon_woland'
READS = json.loads((HERE/'numbered_000_050_reads.json').read_text())
CENSUS = json.loads((HERE/'numbered_000_050_census.json').read_text())
DUPLICATES = json.loads((HERE/'numbered_000_050_duplicates.json').read_text())
SMOKE = json.loads((HERE/'numbered_000_050_smoke.json').read_text())
REGISTRY_PATH = ROOT/'dag/workflows_dag.json'
REGISTRY = json.loads(REGISTRY_PATH.read_text(encoding='utf-8'))
FAMILIES = {n['id']:n for n in REGISTRY['nodes'] if n.get('kind') == 'existing_workflow_family'}
REGISTRY_LINES = REGISTRY_PATH.read_text(encoding='utf-8').splitlines()
FAMILY_RANGES = {}
for key in FAMILIES:
    start = REGISTRY_LINES.index(f'      "id": "{key}",')
    end = next(j for j in range(start+1,len(REGISTRY_LINES)) if REGISTRY_LINES[j] in ('    },','    }'))
    FAMILY_RANGES[key] = [start, end+1]

# contribution; mathematical basis; family IDs; verdict; substantive rationale; next action
ROWS = [
(0, 'Historical dialect/answer-slot and operator-licensing campaign on one linear system.',
 'Exact integer answer admission after a two-variable rational solve; empirical observations are separate from the host oracle.',
 'WF1 WF3 WF6 WF19', 'duplicate_candidate',
 'The 31 completed response records support a historical artifact corpus, not a new workflow family or a newly sealed benchmark. The current shared linalg gate compares against a supplied oracle integer; it does not itself establish that the prompt encoding preserves the equations. Hundreds of files are already byte-identical in WF6.',
 'Keep observation provenance and the answer-channel failure examples; consolidate only after preserving a manifest-backed alias to WF6 and testing transfer on genuinely new cases.'),
(1, 'Separate problem, candidate and contract digests, plus span-local edit detection.',
 'SHA-256 equality detects changed serialized objects; a resealed wrong candidate still passes digest equality.',
 'WF6 WF8 WF23', 'duplicate_candidate',
 'The local trial explicitly separates custody from truth using a resealed edge-count lie. This is a useful negative control for existing sealed-packet workflows, not a separate graph mechanism. Most local response capsules are planned or refused; only one contains a raw reply.',
 'Port the resealed-lie and span-localization controls into the canonical custody tests; retain the historical source/response lineage.'),
(2, 'Token allowlist demonstration framed as constrained decoding.',
 'Finite alphabet membership plus the cycle rank change m-n+c after adding one chord.',
 'WF6 WF9', 'stub_candidate',
 'masked() filters a supplied string; neither logits nor KV-cache hooks are accessed. The code marks the mode winning condition unexecuted. A string within the alphabet can still name an invalid repair. Existing capsule bytes also overlap WF6.',
 'Archive as an unexecuted decoding-hook proposal or reduce to a parser negative fixture; require a real constrained-decoding adapter and semantic checker before promotion.'),
(3, 'Detect an invented length for an absent graph edge while preserving a typed refusal.',
 'A local structural predicate on status and missing-edge membership; one good and two bad constructed examples.',
 'WF7 WF14 WF41', 'duplicate_candidate',
 'The structural predicate is better than the demonstrated word search, but the small prewritten self/failure panel is not detector adequacy or transferred immune learning. All response records are PLANNED or TYPED_REFUSAL with no raw reply.',
 'Use the supplied counterexample in WF14/WF41 self-tolerance and held-out detector tests; do not count this as a live immune system.'),
(4, 'Named parse/eliminate/report composition on one rational linear system.',
 'Both displayed parenthesizations call the same solve_linear(rows) and ignore the grouping argument operationally.',
 'WF4 WF20', 'trivial_candidate',
 'The alleged associativity check changes only a label. Cycle and color failures are hardcoded list/string comparisons, not an actual composition/type checker. It supplies no reusable operad implementation beyond mechanisms already intended by the registered families.',
 'Keep one explanatory counterexample if useful; remove this as a distinct mechanism candidate after provenance is preserved. A genuine extraction needs typed operations and composition laws tested on actual operation graphs.'),
(5, 'Premise-citation demonstration for a three-step graph-fact trace.',
 'One connectedness claim cites a supplied component count; cycle rank is independently computable for the four-edge square.',
 'WF20 WF42', 'duplicate_candidate',
 'The certified trace tests a fixed premise list and computed component value; it does not replay arbitrary submitted derivations. A missing-premise object is labeled a ghost step by construction. Fifty response capsules are NOT_RUN.',
 'Retain the missing-premise negative control under a real trace replay owner such as pilot34/WF42; avoid keeping a second workflow wrapper.'),
(6, 'Same invariant with different graph repairs; selected relabeling and braid examples.',
 'Cycle rank m-n+c; adjacent swaps on three labels satisfy the displayed braid word. orient(order) compares only the first two labels.',
 'WF9 WF10 WF17', 'trivial_candidate',
 'Equal rank does not select a repair, a useful general lesson. But orient is not permutation parity: the even permutation [2,0,1,3] yields -1. The source tests only chosen permutations, so it cannot support its broader orientation wording.',
 'Retain the equal-invariant/different-repair counterexample under WF10; replace the orientation demonstration only in a future authorized implementation, not by promoting this capsule.'),
(7, 'Finite signed-pair cancellation presented alongside a refusal.',
 's(x)w(x)+s(Xi(x))w(Xi(x))=0 for the supplied two-element equal-weight opposite-sign pair.',
 'WF7 WF13', 'trivial_candidate',
 'The arithmetic is elementary and the predicate does not check Xi squared equals identity for arbitrary input; a four-cycle with alternating signs can satisfy its local checks. The supplied pair is valid, but it is not a reusable involution verifier or new refusal workflow.',
 'Keep a single cancellation fixture if needed; require explicit totality, bijection and involution checks before reusing the predicate.'),
(8, 'Proof-text preflight for sorry and an out-of-list axiom name.',
 'Exact solution of a small system plus substring tests; no elaboration or kernel proof check.',
 'WF13 WF16', 'stub_candidate',
 'The declared Lean kernel winning condition is explicitly not run. A matching theorem sentence and named whitelist cannot substitute for a kernel receipt. Fifty response capsules are NOT_RUN.',
 'Keep as a negative demonstration that text scanning is not proof verification; discard the executable-workflow claim unless a pinned Lean invocation is supplied.'),
(9, 'Replay a known rejected tree claim and detect an amnesiac checker.',
 'A graph with cycle rank one is not a tree; byte digest guards the stored candidate.',
 'WF14 WF18 WF19', 'duplicate_candidate',
 'A real reusable regression principle is present, but the historical_checker and amnesiac comparators are tiny purpose-built functions over one fixed graph. No external failure archive or transfer test is exercised.',
 'Move the stale-rejection and changed-digest cases into the canonical replay/immune regression suite, retaining source references.'),
(10, 'Abstain when a route request permits incompatible discrete and metric readings.',
 'Two declared interpretations have unequal outputs and neither has a selected license.',
 'WF7 WF15', 'stub_candidate',
 'The collision is supplied, not detected from arbitrary language. The advertised thirteen gates are absent and the winning condition is explicitly unexecuted. A local abstention fixture remains useful.',
 'Fold the ambiguity/refusal fixture into WF7; leave the tribunal proposal unimplemented until gates and testable interpretations are defined.'),
(11, 'Positive versus degenerate triangle check using squared side lengths.',
 '16 A^2 = 2ab+2ac+2bc-a^2-b^2-c^2; values 48 and 0 in the two supplied examples.',
 'WF7 WF13 WF10', 'domain_specific_candidate',
 'This is an exact domain predicate, not a new PFP workflow. It neither computes general Regge geometry nor derives Bianchi identities. Later triangle owners already provide wider explicit input validation.',
 'Keep as a compact geometry/refusal fixture under the existing domain battery; consolidate with triangle_angle_defects rather than retaining a separate workflow.'),
(12, 'Lossy projection/join example beside a redundant linear equation.',
 'Natural join of AB and BC can introduce spurious tuples when B is not a key; retaining the full key recovers the example.',
 'WF16 WF21 WF34 WF46', 'trivial_candidate',
 'The loss counterexample is useful. The claimed confluence component compares two prewritten frozensets; it runs no rewrite or chase system. The one-row recovery uses a relation retaining all attributes, so no general normalization engine is established.',
 'Keep the spurious-tuple counterexample as a protected-query loss test; remove normalization/confluence-engine claims from future summaries.'),
(13, 'Typed refusal with an unchanged-state digest.',
 'A query names a vertex outside the finite carrier; rejected state mutation changes the digest.',
 'WF7 WF39', 'duplicate_candidate',
 'Refusal and protected-state preservation are separate obligations worth retaining, but these are fixed local objects and an existing WF7/WF39 concern, not a live exception-handling mechanism.',
 'Consolidate into typed-refusal invariants, with one control that returns the correct code but corrupts state.'),
(14, 'Scripted display/solver synchronization and keybinding lookup.',
 'Compare two supplied phi values and membership in a fixed keybinding map.',
 'WF9 WF13', 'stub_candidate',
 'No terminal renderer or interactive state loop is launched. The live-board winning condition is false. A preconstructed after-state cannot establish UI synchronization under actual events.',
 'Archive as an unexecuted UI proposal; retain a test only if a real interactive adapter later consumes it.'),
(15, 'Remove-and-reinsert schedule versus deleting all boundary edges.',
 'A fixed ten-step schedule preserves an edge multiset because every removed edge is immediately restored.',
 'WF9 WF26', 'trivial_candidate',
 'Closure follows directly from the programmed operation. The environment is explicitly nonstochastic and the advertised stochastic winning condition is unexecuted; this is no evidence of adaptive recovery.',
 'Do not make a workflow family from this schedule; keep at most a baseline example for a later externally generated perturbation test.'),
(16, 'Three matching examiner records with residual fields.',
 'One exact elimination yields a=2,b=1; three records repeat vote 3 and residual 0.',
 'WF4 WF15 WF28', 'trivial_candidate',
 'The source itself acknowledges repeated local elimination, not independent examinations. Supplied residual fields are not independently recomputed per examiner. Agreement, missing evidence and dissent are demonstrated only by constructed records.',
 'Prefer pilot35 role-submission checking; keep this as a warning that repeated output is not independent evidence.'),
(17, 'Boundary against treating a graph count or rounded number as a basis certificate.',
 'K6 has 15 edges; a supplied finite decimal squared is not 1/6; a dimension-two ratio is a separate example.',
 'WF7 WF13', 'stub_candidate',
 'No candidate dimension-six basis is checked and the named winning condition is false. The broad mathematical question in the historical contract is not investigated by this pilot. The tautological text check is not a classifier of unsupported claims.',
 'Retain the exact-versus-rounded negative fixture if useful; do not retain this as a MUB solver or new workflow.'),
(18, 'Distinct labels and an edge contrasted with identified labels.',
 'A supplied two-vertex one-edge graph has one component and cycle rank zero; two strings are unequal by construction.',
 'WF17 WF16', 'trivial_candidate',
 'The code supplies the two marks, finite graph, comparison and arithmetic. It does not derive irreflexivity, a carrier or an operation from the inscription <>. A stated prohibition on coordinates is not an executable derivation.',
 'Keep only as a bounded counterexample about label identification, with all supplied structure explicit; do not promote it into a Genesis mechanism.'),
(19, 'Receipt-only verdict and bounded debate illustrated on a missing edge.',
 'Equality of a refusal code/state digest and the integer inequality 4>3.',
 'WF7 WF15 WF45', 'duplicate_candidate',
 'No proposer/adversary model separation exists. The source constructs a terminal receipt and tests a constant beyond-cap round. This demonstrates the intended policy but does not implement a debate controller.',
 'Consolidate the no-receipt and over-cap controls into the existing terminal-selector/tribunal implementation.'),
(20, 'Two-stage binding that rejects a stale first-stage citation despite a correct answer.',
 'A second-stage object must cite SHA-256 of the exact first-stage system; exact solve gives x+y=3.',
 'WF8 WF23', 'duplicate_candidate',
 'The stale-citation/right-number counterexample is reusable. It is the same stage-binding mechanism already registered in WF8, with no model calls and no new workflow variation requiring its own owner.',
 'Retain the stale-citation control in WF8 and merge duplicate packet helpers after provenance mapping.'),
(21, 'Explicit edge ownership for two spans sharing a vertex.',
 'Disjoint edge subsets partition a carrier with two independent cycles; digests localize an edge moved between owners.',
 'WF8 WF23 WF32', 'duplicate_candidate',
 'This refines custody granularity, but the spans are supplied and edge-disjoint. It is a test fixture for ownership accounting, not a general overlapping-span resolution algorithm.',
 'Add the shared-vertex/unique-edge-owner case to custody tests; require an explicit ambiguity policy before handling genuinely shared edges.'),
(22, 'Witnessed glyph packet contrasted with a bare legal glyph string.',
 'A fixed E,I,D,C,T list carries a solved linear-system witness and zero sum residual.',
 'WF20 WF42', 'stub_candidate',
 'The eight-glyph alphabet and witnesses are local examples; no DDC state machine executes. Winning condition is false. The source tests the prepared values rather than replaying arbitrary state transitions.',
 'Use pilot34 as the stronger reusable owner for transition replay; retain a bare-tape negative fixture only.'),
(23, 'Seal a linear system and record a variable-name rotation.',
 'Digest equality binds row bytes; rotation leaves the sum invariant, while replacing rows can keep the sum but change the solution.',
 'WF6 WF8 WF49', 'duplicate_candidate',
 'The code does not implement an actual renaming action on equations; it supplies a permuted-name list. Its changed rows give [6,0,0], also sum 6, so answer equality alone cannot establish data fidelity. The seal detects the byte change.',
 'Keep the same-answer/different-data control in WF49; consolidate packet code with WF8.'),
(24, 'Second invocation of the same witnessed-glyph builder used by pilot22.',
 'Identical _glyph_trials implementation and mode 01, differing only in pilot identifier/coordinate metadata.',
 'WF20 WF42', 'duplicate_candidate',
 'This is an exact semantic repeat of pilot22 rather than a new mechanism. Neither executes the DDC state machine.',
 'Select one historical representative and preserve both provenance pointers; remove duplicate runnable ownership only after approval of a concrete consolidation.'),
(25, 'Sealing a witnessed glyph packet and a deliberately witness-free tape.',
 'The same glyph builder as pilots22/24 plus the fact that hashes can consistently seal an invalid semantic object.',
 'WF8 WF20 WF42', 'duplicate_candidate',
 'The added sealed-bare-tape control reinforces custody versus validity, already demonstrated in pilot1. It neither adds a transition checker nor validates the language beyond the supplied examples.',
 'Retain one sealed-invalid-object control under WF8 and one bare-tape control under WF42; avoid a third glyph workflow wrapper.'),
(26, 'Finite XOR obstruction, all minimum edge repairs, and relabeling checks.',
 'On a three-cycle over F2, compatibility is parity of edge labels; exhaustive eight assignments and all one-edge repairs are feasible.',
 'WF9 WF10', 'duplicate_candidate',
 'This is a substantive finite obstruction checker with an independent parity test, but run.py is byte-identical to workflows/tasks/xor_cycle_obstruction/run.py. It is a domain instance of an existing family.',
 'Keep the canonical task owner and its exhaustive parity/repair tests; preserve import provenance before removing duplicate ownership.'),
(27, 'Primal/dual certificates and strictly decreasing duality-gap traces.',
 'For nonnegative x and lambda, Ax<=b and A^T lambda>=c imply c^T x<=b^T lambda; feasible equality certifies optimality.',
 'WF11 WF20', 'duplicate_candidate',
 'The checker tests feasibility, dual signs/domination and objective equality rather than trusting a gap field. Tests include zero-gap but infeasible counterexamples and a finite independent trace grid. The source is already byte-identical to the lp_certificates task owner.',
 'Retain primal/dual and nonuniqueness certificates in the canonical WF11 task; keep trace refinements as a bounded variant, not another solver family.'),
(28, 'Strict full-consumption parsers for four explicit glyph/packet profiles.',
 'Recursive grammar recognition with byte/depth/node bounds; grammar acceptance and resource-limit refusal are distinct.',
 'WF6 WF16 WF21', 'duplicate_candidate',
 'Source and independent EBNF-comparison tests give a reusable syntax boundary. Syntax is not semantic correctness, and a digest-shaped field does not authenticate a packet. run.py already exactly matches grammar_profiles.',
 'Use the canonical grammar task and preserve the independent EBNF oracle; do not treat accepted syntax as an admitted semantic operation.'),
(29, 'Integral obstruction and explicit rational carrier lift.',
 'z is in mZ iff m divides z; nearest integer multiples give exact residual minima. Triangle identities Dg=0, pg=1 and I-gp=AD certify the stated rank-one kernel.',
 'WF10 WF20', 'duplicate_candidate',
 'The code distinguishes a rational solution from an integral one and requires a kernel identity, with an adversarial zero-matrix test. It is an existing exact task byte-for-byte, not a derivation of a general cohomology engine.',
 'Keep integer-obstruction and scope-changing lift witnesses in the canonical task; avoid claiming the rational witness solves the original integral problem.'),
(30, 'Bounded rewrite normal forms, replay paths, and information-loss counterexamples.',
 'Length-decreasing string rules give termination on the finite explored graph; differing terminal forms disprove confluence for that input.',
 'WF21 WF34', 'duplicate_candidate',
 'run.py is exactly the existing rewrite_normal_form_loss owner. Exploration beyond 1024 states is marked incomplete; a unique observed normal form is not global confluence. No local test .py exists despite README test language.',
 'Consolidate with the existing task and add/locate real confluence, resource-bound and lost-query tests before relying on README validation claims.'),
(31, 'Exact two-path interference and weight-to-square-root representations.',
 'Hadamard action over a restricted Gaussian-rational phase family; equal input magnitudes can yield different output probabilities under a supplied model.',
 'WF13 WF16 WF17', 'duplicate_candidate',
 'The distinction between phase-sensitive evolution and normalized weights is mathematically useful, with rational phase checks. It assumes the transformation and readout model; it does not derive quantum mechanics. Source is identical to interference_weights.',
 'Retain as an explicit-domain fixture in the canonical task; keep imported physical assumptions visible and do not create another workflow family.'),
(32, 'Three-sector normalization and explicitly admitted amplitude readout.',
 'p_i=w_i/sum(w), positive scale invariance, symbolic nonnegative square-root lift, and squared magnitudes under a named readout assumption.',
 'WF13 WF16', 'duplicate_candidate',
 'The implementation and tests distinguish representation from interpretation and reject an absent readout admission. The 999-triple test is a finite check, not a derivation of the Born rule. Source already matches normalization_readout.',
 'Keep the canonical domain fixture and missing-assumption negative controls; consolidate duplicate source.'),
(33, 'Canonical numeric packet profiles, two-stage reply checking, and a persistent simulated budget ledger.',
 'Reduced rational syntax, exact Fraction evaluation, complete tree equality, and reservation exposure accounting with UNKNOWN/BREACH holds.',
 'WF8 WF9 WF16 WF22', 'retain_mechanism',
 'The core goes beyond a wrapper: it separates syntax/value/tree preservation and persists request identity and unresolved charge holds. Its provider type is explicitly ScriptedProvider and billing is offline simulated. These are implementation candidates for existing families, not evidence of live cost control.',
 'Extract canonical numeric codec and ledger invariants into existing owners after a focused dependency/locking audit; keep scripted-provider status explicit and compare against current budget authority before reuse.'),
(34, 'Task-bound witnessed state-transition replay with scoped loss and lift permissions.',
 'Explicit finite state, projected residual and repair witnesses; admitted transitions and task/state hashes enforce the declared word and operation contracts.',
 'WF7 WF20 WF42', 'duplicate_candidate',
 'This is materially stronger than the bare glyph capsules: it recomputes transitions, preserves state on refusal and binds permission to operations. Independent finite residual tests exist. The entire run.py already matches trace_replay_refusal.',
 'Make the existing task the sole execution owner; retain pilot22/24/25 only as historical negative examples pointing here.'),
(35, 'Frozen role submissions with agreement separate from checked truth.',
 'A bounded sum(left)<=sum(right) predicate supplies the only direct mathematical claim check; opaque claims remain unverified.',
 'WF4 WF15 WF28', 'duplicate_candidate',
 'The source actually observes whether the host checker ran and can reject agreeing false proposals. No independent model-role execution is implemented. Existing role_submission_comparison differs only by a comment.',
 'Retain canonical role/binding/refusal tests; use a separate dispatcher if genuine independent blinded submissions are later required.'),
(36, 'Chronological supply/designation/admission provenance and finite observation profiles.',
 'Complete finite observation tables provide separating witnesses; a declared transition relation permits but does not force a next state.',
 'WF16 WF17 WF39', 'duplicate_candidate',
 'This supplies useful admission and non-inference boundaries, including explicit refusal to infer identity or inevitability. Tests enumerate finite relations and profiles. Source exactly matches finite_provenance.',
 'Retain canonical admission-order and task/history-substitution checks; avoid recasting supplied relations as a Genesis derivation.'),
(37, 'Finite quotient factorization, explicit selectors and refinement witnesses.',
 'A function factors through a quotient iff constant on fibres; a new quotient refines an old one only with a checked forgetful map.',
 'WF16 WF17 WF34 WF46', 'duplicate_candidate',
 'The finite algebra and adversarial refinement tests are substantive. Selecting a representative can add information and a supplied admission is not authentication. Source exactly matches finite_quotients.',
 'Retain the canonical quotient/refinement checker as a shared PCIV preservation tool; keep costs and selection relative to declared candidate families.'),
(38, 'Task-stationary checking of ordinary, principal-value and paired singular-integral prescriptions.',
 'Exact rational endpoints and symbolic logarithmic expressions distinguish divergent improper integrals from admitted paired limits.',
 'WF13 WF20 WF27', 'duplicate_candidate',
 'The generalizable part is detecting a change of problem and requiring an explicit fork/admission. The integrator is a narrow simple-pole family with syntactic symbolic-expression equality. Existing singular_integrals is byte-identical.',
 'Retain task-stationarity/fork controls in the generic workflow and keep simple-pole arithmetic as a domain fixture.'),
(39, 'Intrinsic triangle/link validation with exact or explicitly unresolved angle defects.',
 'Rational squared-length Gram determinant; finite vertex-link topology; only selected angle classes have recognized rational multiples of pi.',
 'WF10 WF13 WF20', 'duplicate_candidate',
 'The source preserves UNKNOWN rather than treating unrecognized zero defects as nonzero. Tests supply a true zero outside the recognizer. Existing triangle_angle_defects differs only in a provenance comment.',
 'Consolidate with the task owner, retain unknown-angle and completion-preservation controls, and keep physical interpretations outside acceptance.'),
(40, 'Exact cochain potential/obstruction and declared dual/Hodge adapter.',
 'Signed incidence, d1*d0=0, spanning-forest potential with nonzero cycle witness, and an explicitly positive rational diagonal star.',
 'WF10 WF13 WF16', 'duplicate_candidate',
 'The useful reusable point is closed versus exact and preservation of orientation/adapter assumptions. Existing cochains_hodge_adapter differs only by a comment. No local Python tests accompany the README claims.',
 'Use the canonical task; require located or new independent cycle/orientation tests before treating this imported snapshot as verified.'),
(41, 'Permission-bound inactive-to-active face transition with exact state replay.',
 'A face boundary changes the finite chain image; task/state/operation-bound grants control a single 0-to-1 activation.',
 'WF10 WF20 WF39', 'duplicate_candidate',
 'Replay keeps the last accepted state and stops at refusal; tests check stale grants, repeat activation and boolean/int substitution. Toy mass/drag observables are declared adapters, not physical consequences. Existing face_activation differs only by a comment.',
 'Retain transition-grant and prefix-preservation controls in canonical workflow tests; leave toy physics in optional fixtures.'),
(42, 'Exact finite Hodge decomposition and oriented complement bookkeeping.',
 'Rational orthogonal projection onto boundary images; exact+coexact+harmonic decomposition, chain law and finite energy identities.',
 'WF10 WF13 WF16', 'duplicate_candidate',
 'Independent test helpers compare matrices, ranks, projections and residuals. Existing hodge_decomposition has the same arithmetic/checker mechanism; differences are pilot ID and display vocabulary/comments. The imported core hash also matches pilot46 frozen pin.',
 'Choose one canonical mathematical owner and preserve display/source mappings; do not count it as another general workflow or continuum theorem.'),
(43, 'Finite checkerboard-path histogram and exact complex amplitude calculation.',
 'Dynamic programming over step/direction/corner state; a rational polynomial in the corner weight, checked against small full path enumeration.',
 'WF13 WF16', 'duplicate_candidate',
 'The arithmetic is substantive but domain-specific, bounded to 32 steps, and does not establish a continuum limit or physical probability normalization. Existing checkerboard_paths differs only by a comment.',
 'Keep one domain fixture owner with the independent enumeration test; do not create a workflow family for this task.'),
(44, 'Clique-complex homology with exact ranks and complete Betti-vector checking.',
 'Finite clique enumeration at an explicit cutoff; rational boundary matrices and RREF witness checks; Euler agreement alone is insufficient.',
 'WF10 WF13', 'duplicate_candidate',
 'The same-Euler/wrong-Betti test is a useful checker-adequacy control. Source exactly matches clique_homology, and the operation is a finite domain checker rather than a new orchestration mechanism.',
 'Retain canonical exact-rank witnesses and the weak-invariant counterexample; consolidate duplicate code.'),
(45, 'Equilateral triangle-fan defects and count/weight pairing distinction.',
 'Deficit in turns is 1-n/6 for a checked connected cyclic link; equal positive/negative counts need not cancel unequal weights.',
 'WF10 WF13', 'duplicate_candidate',
 'Source exactly matches triangle_fan_pairing. The finite fan and pairing arithmetic are useful domain tests, not a general geometric or physical theory. No local Python tests exist despite README test claims.',
 'Retain optional fan/pairing fixtures under the canonical task; locate independent tests before relying on validation counts.'),
(46, 'Weighted exact complement companion over a pinned finite Hodge core.',
 'Oriented complement maps use exact square-root weight ratios and the degree/sign formula; edge weights lie in a small declared integer profile.',
 'WF13 WF16', 'domain_specific_candidate',
 'The source and selected 62-basis-face test provide a real narrow algebraic extension. It is not a new PFP orchestration family. The present smoke probe refuses because the old omega_engine_woland ancestor locator cannot resolve; the imported core bytes do match the frozen hash.',
 'Keep as an optional exact-math fixture pending an explicitly reviewed locator/dependency migration; preserve historical pin bytes and avoid silently accepting another core.'),
(47, 'Typed document-span transport with source/query replay and exact intermediate-version composition.',
 'Byte spans bind source and request; arrows preserve a complete executable answer; identity and composition require complete endpoint/span records.',
 'WF16 WF21 WF49', 'retain_mechanism',
 'This is a useful PCIV/OPERADS-adjacent implementation candidate: it validates real maps and composition, unlike pilot4. It proves only preservation of the pinned query, not general semantic equivalence. Current execution refuses the obsolete dependency locator before graph construction.',
 'Extract typed span/query transport into an existing preservation owner after dependency migration and adversarial replay; do not add a new family solely for the Hodge task.'),
(48, 'Reversible nibble-glyph transport, permutation composition, and explicit wire cost accounting.',
 'A permutation group acts on both legend key and glyph string so decode(act(p,packet)) equals original bytes; Horner evaluation supplies a protected finite query.',
 'WF6 WF16 WF21 WF49', 'retain_mechanism',
 'The implementation checks payload bytes as well as equal answers, and tests group laws plus same-answer/different-task and whitespace controls. Default pure-function probe returns PRESERVED with zero calls. Byte/codepoint measurements are not token measurements or evidence of model reasoning improvement.',
 'Extract a codec and preservation/cost test fixture into existing dialect/query-preservation owners; preserve the explicit no-authentication/no-token claims.'),
(49, 'Bounded replay of supplied replies with typed outcome classification and early stop.',
 'Exact bounded integer addition; at most three attempts, first valid task-bound answer terminates, unused tail is not parsed.',
 'WF1 WF7 WF9', 'duplicate_candidate',
 'A sound small fixture for controller behavior, but responses are supplied in advance and provider_calls is fixed zero. No repair proposal is generated. The default replay accepts 42 at zero calls; WF9 already owns bounded repair.',
 'Keep malformed/wrong-task/abstain/limit/tail controls in WF9; archive the separate pilot wrapper after preserving lineage.'),
(50, 'One-pass template substitution versus sequential replacement of inserted data.',
 'Literal data containing ${question} must remain literal; concatenation oracle checks the rendered bytes.',
 'WF21 WF39', 'duplicate_candidate',
 'This is a useful injection/fidelity regression fixture, not a general prompt-improvement algorithm. Source exactly matches template_substitution; default pure-function probe demonstrates the differing outputs at zero calls.',
 'Retain the canonical template regression test; consolidate the duplicate pilot runner.'),
]

SHARED = f'{BASE}/replay_runners/mode_capsules/'
MODE_RANGES = {
1:('trials_01_12.py',28,119),2:('trials_01_12.py',122,175),3:('trials_01_12.py',178,215),4:('trials_01_12.py',218,271),
5:('trials_01_12.py',274,310),6:('trials_01_12.py',313,373),7:('trials_01_12.py',376,434),8:('trials_01_12.py',437,481),
9:('trials_01_12.py',484,533),10:('trials_01_12.py',536,576),11:('trials_01_12.py',579,621),12:('trials_01_12.py',624,689),
13:('trials_13_25.py',25,65),14:('trials_13_25.py',68,109),15:('trials_13_25.py',112,169),16:('trials_13_25.py',172,221),
17:('trials_13_25.py',224,265),18:('trials_13_25.py',268,307),19:('trials_13_25.py',310,351),20:('trials_13_25.py',354,393),
21:('trials_13_25.py',396,443),22:('trials_13_25.py',446,522),23:('trials_13_25.py',525,560),24:('trials_13_25.py',446,518),25:('trials_13_25.py',567,581)}
NEAR = {35:'role_submission_comparison',39:'triangle_angle_defects',40:'cochains_hodge_adapter',41:'face_activation',42:'hodge_decomposition',43:'checkerboard_paths'}
MECHANISMS = [
 'answer_slot_schema_and_operator_licensing','digest_sealed_four_object_envelope','text_token_allowlist_only',
 'structural_missing_carrier_detector','composition_label_demo_only','premise_citation_fixture',
 'same_invariant_distinct_repairs','declared_signed_pair_cancellation','proof_text_preflight_only',
 'rejected_candidate_regression_replay','explicit_interpretation_collision_refusal','squared_triangle_degeneracy_gate',
 'lossy_join_counterexample','refusal_state_preservation','scripted_display_sync_fixture',
 'remove_restore_schedule_only','repeated_examiner_record_fixture','exact_decimal_boundary_fixture',
 'supplied_distinct_marks_fixture','receipt_only_terminal_policy_fixture','stage_digest_binding',
 'explicit_span_edge_ownership','witnessed_glyph_fixture_without_replay','same_answer_changed_data_custody',
 'duplicate_witnessed_glyph_fixture','sealed_invalid_trace_counterexample','finite_xor_obstruction_and_minimum_repairs',
 'primal_dual_certificate_and_gap_trace','strict_profile_parser_with_limits','integral_obstruction_and_explicit_lift',
 'bounded_normal_forms_and_loss_witness','phase_sensitive_exact_interference','normalization_with_explicit_readout_admission',
 'canonical_numeric_packet_staging_and_offline_reservation_ledger','task_bound_witnessed_transition_replay',
 'frozen_role_submissions_with_independent_host_predicate','chronological_admission_and_observation_profiles',
 'quotient_factorization_and_refinement_witness','problem_stationarity_and_declared_prescription_fork',
 'finite_link_metric_validation_with_unknown_angle_outcome','cochain_potential_and_cycle_obstruction',
 'permission_bound_face_activation_replay','finite_exact_hodge_decomposition','finite_path_histogram_certificate',
 'clique_homology_rank_witnesses','finite_fan_defect_and_weighted_pairing','pinned_weighted_complement_adapter',
 'typed_span_transport_and_query_preserving_composition','reversible_glyph_group_action_and_wire_costs',
 'bounded_supplied_reply_replay','single_pass_literal_template_substitution',
]

def digest(path):
    return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()

def evidence(path, start, end, level):
    return {'path':path,'lines':[start,end],'sha256':digest(path),'review_level':level}

records = []
for i, contribution, math, wf, verdict, rationale, action in ROWS:
    path = f'{BASE}/pilot_{i:07d}'
    ev = [x for x in READS if x['path'].startswith(path+'/')]
    if i in MODE_RANGES:
        file,a,b = MODE_RANGES[i]
        ev.append(evidence(SHARED+file,a,b,'selected_owner_and_embedded_predicates_read'))
        if i in (24,25):
            ev.append(evidence(SHARED+'trials_13_25.py',446,518,'selected_shared_builder_read'))
        ev.append(evidence(SHARED+'packet.py',120,162,'shared_result_constructor_read'))
    if i <= 4:
        ev.extend(x for x in READS if x['path'] in (f'{BASE}/live_evaluator.py',f'{BASE}/offline_evaluator.py','pfp/domain/pilots/fail_closed_gate.py'))
    for e in CENSUS[i]['execution_records']:
        ev.append({k:e[k] for k in ('path','lines','sha256','review_level')})
    duplicate = DUPLICATES[i]
    owner_matches = [m for m in duplicate['matches'] if m['path'] == path+'/run.py']
    near = None
    if i in NEAR:
        original = f'workflows/tasks/{NEAR[i]}/run.py'
        near = {'path':original,'sha256':digest(original),
                'comparison':'Only comment wording differs.' if i != 42 else 'Same arithmetic/checker code; pilot identifier, source vocabulary and fixture display strings differ.'}
    status = {
      'audit_model_calls':0,
      'audit_full_test_suite_run':False,
      'historical_readme_test_counts':'Claims only; not reproduced in this triage.',
      'response_schema_census':{k:CENSUS[i][k] for k in ('response_count','statuses','modes','nonempty_raw_reply_count')},
      'test_sources_present':CENSUS[i]['python_test_files'],
    }
    if i <= 25:
        status['mechanism_execution'] = 'Historical response corpus plus offline local predicates; retired live dispatch refuses new calls.' if i <= 4 else 'Stored local offline execution record; provider_calls=0. No fresh replay run in this audit.'
        status['recorded_mode_winning_condition'] = [e['winning_condition_executed'] for e in CENSUS[i]['execution_records']]
        status['ceiling'] = 'Parsed response metadata does not authenticate historical provider dispatch, billing, correctness, or independence. ACCEPTED/claim_held is not an adequacy certificate.'
    else:
        status['mechanism_execution'] = 'Offline deterministic source and selected tests inspected; no live provider integration demonstrated.'
        if i in (30,40,45):
            status['missing_test_evidence'] = 'No local test*.py under tests; README test claims not confirmed.'
    status['current_smoke_probe'] = next((r for r in SMOKE if r['pilot']==i),None)
    mappings = [{'family_id':key, 'path':FAMILIES[key]['path'],
                 'registry_source_evidence':evidence('dag/workflows_dag.json',*FAMILY_RANGES[key],'selected_family_node_process_math_and_sources_read'),
                 'relationship':'Existing family; source-specific fixture/implementation candidate, not evidence for a new independent family.'} for key in wf.split()]
    transfer = {
      'protected_qm_seed_read':False,
      'mathematical_support_for_unchanged_qm_seed':'NOT_ESTABLISHED',
      'requires_seed_appropriate_checker_or_encoding':True,
      'prerequisite':'Supply or independently match a declared QM task encoding, mathematical predicate/certificate checker and negative controls. The current finite task checker cannot certify an unspecified QM result.',
      'reusable_without_claiming_qm_correctness':'The named custody, parsing, replay or control mechanism may be reused within its explicit bounds after matching interfaces; workflow transfer alone is not mathematical transfer.',
    }
    if i in (31,32):
        transfer['prerequisite'] = 'The current checker covers only its declared two-path/three-sector model and explicit readout assumptions. A different QM task requires a matching model/certificate encoding and independently checked predicates; the protected seed was not inspected for compatibility.'
    elif i == 33:
        transfer['prerequisite'] = 'The current grammar evaluates canonical rationals and six-operand sums only. QM transfer needs an explicit typed mathematical vocabulary/checker; the reservation ledger can be evaluated separately as an offline control invariant.'
    elif i == 47:
        transfer['prerequisite'] = 'Replace the hardcoded entire_pilot21_answer adapter only through a reviewed new declared QM query/checker and dependency pins. Span preservation by itself proves no QM claim; fix the current obsolete locator in a separately reviewed migration.'
    elif i == 48:
        transfer['prerequisite'] = 'The current decoded Query schema is a bounded polynomial task. Generic byte transport requires a new declared payload adapter/encoding; QM acceptance additionally needs its own independent certificate checker. Byte counts cannot be promoted to token or performance gains.'
    records.append({'id':f'pilot_{i:07d}','path':path,'contribution':contribution,'mathematical_basis':math,
                    'reusable_mechanism_name':MECHANISMS[i], 'qm_seed_transfer':transfer,
                    'actual_execution_status':status,'source_evidence':ev,'workflow_mapping':mappings,
                    'duplicate_evidence':{'eligible_files_matching_existing_pfp':duplicate['matched_files'],
                                          'eligible_files_without_baseline_match':duplicate['no_match_files'],
                                          'exact_run_py_matches':owner_matches,'near_duplicate_owner':near,
                                          'full_matches_file':'dag/pilot_triage/numbered_000_050_duplicates.json'},
                    'verdict':verdict,'rationale':rationale,'next_action':action})

counts = dict(collections.Counter(r['verdict'] for r in records))
report = {
 'schema':'pfp.imported-pilot-triage.v1',
 'scope':'Numbered imported pilots 0000000 through 0000050 inclusive; all 51 primary README entries and available primary spec.yaml files read.',
 'status':'complete_first_substantive_triage_not_full_estate_certification',
 'authority_effect':'None; recommendations only. No imported file deletion, rewrite, repair or live call performed.',
 'summary':{'pilot_count':len(records),'verdict_counts':counts,'new_workflow_families_recommended':0,
            'retained_mechanism_candidates':['pilot_0000033','pilot_0000047','pilot_0000048'],
            'current_missing_dependency_locators':['pilot_0000046','pilot_0000047'],
            'missing_local_test_sources_despite_readme_claims':['pilot_0000030','pilot_0000040','pilot_0000045']},
 'review_method':[
   'Full primary README and spec.yaml text reads for all 51 entries; exact file/range hashes accompany each pilot.',
   'Selected core implementation/checker functions and selected mathematical/adversarial test bodies read for later pilots. This is not a claim that every Python file, entire test suite, receipt, or historical transcript was fully read.',
   'Early mode capsules reviewed through all 25 shared owner builders and embedded predicates; public response.yaml/execution.yaml records received a schema-field census, not full prose/trace review.',
   'Current existing PFP duplicates were found using dag/file_inventory.json as a candidate index, then rehashed from disk; sensitive seed/private/key-named files were excluded from that comparison. Absence from this baseline is not proof of uniqueness.',
   'The 49 registered existing workflow-family nodes were compared by process/math/source mapping; generated composition nodes were not treated as independent families.',
   'Read-only pure-function smoke probes for 46-50 ran with bytecode generation disabled. No CLI artifact-writing route or full test suite was run.',
   'No seed/private-key input file was opened, no model was called, and historical expected answers were not designated as a new sealed benchmark.',
 ],
 'evidence_limits':[
   'Generated claim_held booleans are assertions about supplied demonstrations. Some positive/negative labels are assigned directly rather than produced by a general checker.',
   'Custody hashes, checker acceptance, detector adequacy, model efficacy and physical interpretation remain separate claims.',
   'Test names/counts and README validation statements are historical claims unless specifically identified as a fresh smoke probe.',
   'No external literature search or novelty comparison was performed; new means locally reusable relative to this registry, not research invention.',
   'Known obsolete monorepo imports/locators remain unchanged. Current failure of 46/47 is observed; other imported entrypoints were not comprehensively executed.',
   'Legacy evaluator imports still name omega_engine_pfp/omega_engine_woland. pfp/domain/pilots checker source was inspected as the current canonical comparison owner; runtime resolution of those old imports was not established.',
 ],
 'context_evidence':[evidence(f'{BASE}/README.md',1,len((ROOT/f'{BASE}/README.md').read_text(encoding='utf-8').splitlines()),'full_context_text_read'),
                     evidence(f'{BASE}/MODUS_OPERANDI.md',1,len((ROOT/f'{BASE}/MODUS_OPERANDI.md').read_text(encoding='utf-8').splitlines()),'full_context_text_read')],
 'registry_evidence':{'path':'dag/workflows_dag.json','sha256':digest('dag/workflows_dag.json'),
                      'review_scope':'49 existing_workflow_family nodes; generated composition nodes excluded'},
 'supporting_artifacts':['dag/pilot_triage/numbered_000_050_reads.json','dag/pilot_triage/numbered_000_050_duplicates.json',
                         'dag/pilot_triage/numbered_000_050_census.json','dag/pilot_triage/numbered_000_050_smoke.json',
                         'dag/pilot_triage/numbered_000_050_validation.json'],
 'pilots':records,
}
(HERE/'numbered_000_050.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

lines = ['# Numbered imported pilots 000–050: first substantive triage','',
         'All 51 primary entries were read. This review recommends **no new workflow family**: most useful material fits existing families or task owners. The three extraction candidates are the offline packet/budget invariants in **033**, typed span/query transport in **047**, and reversible glyph transport in **048**. These are recommendations for review, not completed extraction or deletion.','',
         '**Verdicts:** '+', '.join(f'{k}: {v}' for k,v in counts.items())+'.','',
         'No imported material was changed. No seed/private-key file was read and no model was called. Historical expected answers remain historical evidence, not a newly sealed benchmark.','',
         '## What the evidence supports','',
         '- Exact duplicate task owners exist for 026–032, 034, 036–038, 044, 045 and 050. Owners 035, 039–041 and 043 differ from existing tasks only in comments; 042 also differs in identifier and display vocabulary. The separate duplicate ledger records current SHA-256 matches.',
         '- Early capsules mix historical responses, planned records and local constructed predicates. Pilot000 has 31 COMPLETED records with raw replies; pilots001/002/004 each have only one raw-reply record, and pilot003 has none. Pilots005–010 each have 50 NOT_RUN records. The execution records for 005–025 all declare zero provider calls. These are schema observations, not authentication of historical transport or proof of efficacy.',
         '- Several early mechanisms are incomplete or too weak for their labels: 004 does not operationally compose different parenthesizations; 008 runs no Lean kernel; 012 compares hardcoded sets rather than a rewrite/chase system; 014 opens no terminal; 016 repeats one calculation; 022/024 run no state machine.',
         '- Pilot046 and 047 currently refuse missing old monorepo dependency locators. The imported 042 core does match the frozen hash, so the observed failure is not evidence of current core hash drift. No locator was repaired.',
         '- Pilots030, 040 and 045 have no local Python test files despite README validation wording. Other later pilots have substantive selected mathematical/adversarial test bodies; their entire suites were not rerun.',
         '- Pure-function probes: 048 default PRESERVED at zero calls; 049 default ACCEPTED (42) at zero calls; 050 demonstrates the template difference at zero calls. These probes cover only the selected defaults.',
         '', '## Review limits','',
         'Primary README/spec text was read in full. Core owner/checker functions and selected test bodies were inspected; every file and historical transcript was not fully read. Early generated capsules were reviewed through all shared builders, embedded predicates and a mechanical response/execution schema census. A generated ACCEPTED or claim_held field is not itself a checker-adequacy certificate. Physical models, supplied admissions, finite checks and broader claims remain distinct. No claim of literature novelty is made.','',
         '**QM transfer:** none of these pilots establishes mathematical acceptance for the unread protected QM seed. Each record names the reusable mechanism and the needed checker/encoding contract. Custody, parsing and replay can transfer as control mechanisms only after matching their interfaces and limits; a QM certificate needs a declared, independently checked mathematical predicate. Pilots033/047/048 have specific current grammar/query restrictions, recorded per pilot.','',
         'Detailed path/range/SHA evidence, exact duplicate matches and execution limits are in [the JSON report](numbered_000_050.json), [read ledger](numbered_000_050_reads.json), [duplicate ledger](numbered_000_050_duplicates.json), [schema census](numbered_000_050_census.json) and [smoke probes](numbered_000_050_smoke.json).','',
         '## Per-pilot recommendations','',
         '| Pilot | Verdict | Existing families | Contribution |', '|---|---|---|---|']
for r in records:
    number = int(r['id'].split('_')[1])
    lines.append(f"| {number:03d} | {r['verdict']} | {', '.join(m['family_id'] for m in r['workflow_mapping'])} | {r['contribution']} |")
for r in records:
    number = int(r['id'].split('_')[1])
    lines += ['',f"### {number:03d} — {r['verdict']}",'',r['contribution'],'',
              '**Mechanism.** `'+r['reusable_mechanism_name']+'` → '+', '.join(m['family_id'] for m in r['workflow_mapping'])+'.','',
              '**Basis.** '+r['mathematical_basis'],'','**Finding.** '+r['rationale'],'',
              '**Next action.** '+r['next_action'],'','**QM transfer.** '+r['qm_seed_transfer']['prerequisite'],'']
    key_sources = [x for x in r['source_evidence'] if x['path'].endswith('README.md') or x['path'].endswith('/run.py') or 'trials_' in x['path'] or x.get('review_level')=='selected_test_body_emitted_for_review']
    refs=[]
    for x in key_sources:
        ref = f"`{x['path']}:{x['lines'][0]}–{x['lines'][1]}`"
        if ref not in refs:
            refs.append(ref)
    lines += ['**Evidence.** '+'; '.join(refs)+'.']
(HERE/'numbered_000_050.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps(report['summary'],indent=2))
