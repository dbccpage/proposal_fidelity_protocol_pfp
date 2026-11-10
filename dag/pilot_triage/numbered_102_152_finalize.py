"""Assemble the completed, manually assessed 51-pilot triage and validate custody.

This file does not infer semantic review from parsing. Its assessments record
the source reads performed during the audit. It writes only this report prefix.
"""
from pathlib import Path
from collections import Counter
import difflib
import hashlib
import json
import re
import subprocess

from numbered_102_152_helper import ROOT, BASE, TEMPLATE, info, replacements

PREFIX = ROOT / "dag/pilot_triage/numbered_102_152"
PIN = "8050c66900899771766f33e8f5fdd200b7dd9120"
assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == PIN

# Each entry: proposed mathematical contribution, precise limiting premise,
# canonical family comparison, concrete next action. All are human assessments.
ASSESS = {
102: ("Modular bit-vector program equivalence at a declared width, plus a length bound. Width-8 exhaustive evaluation is a finite proof relative to the interpreter; neither shortening nor sampled agreement proves minimality.", "The wrapper supplies no program. The external implementation uses deterministic samples for widths 16/32/64, contrary to the challenge's width-32 DRAT/LRAT requirement; a valid promised-shortenable public toy case passes both checkers with an inequivalent candidate.", [13,17,44], "Preserve this catalog alias to C058; bind the canonical owner and require proof-producing wide-word equivalence or explicitly restrict acceptance to the exhaustive carrier before reuse."),
103: ("Relational algebra with Kleene three-valued predicates, bag multiplicities, NULL preflight and result headings. Two separate evaluation algorithms compare candidate SQL on supplied finite databases.", "The wrapper has no database or SQL. The current owners both execute candidate SQL with SQLite; this is neither the proposed SQLite-plus-DuckDB run nor universal query equivalence. TEXT affinity versus Python equality produces a reproduced checker disagreement.", [13,11,19], "Preserve this alias to C059; pin SQL typing/coercion, stop on judge disagreement, and bind a declared database panel and owner versions before any dispatch."),
104: ("For rational d0, omega and positive weights, r=omega-d0*alpha, d0^T*y=0, |y|<=w and y^T*omega=sum(w*|r|) certify weighted-L1 optimality by weak duality. Mutation kill and false-rejection rates measure a finite checker panel.", "The wrapper supplies no certificate. The first external scorer trusts fixture expected labels; the independent owner recomputes equations. Zero-column, canonical-string and exception boundaries fail the public contract in toy probes. Finite mutation survival is not universal checker correctness.", [29,11,44,41], "Preserve this C060 alias; reconcile parser/dimension/rejection-code contracts and validate both owners on explicit positive and hostile panels before using this checker-synthesis preset."),
105: ("Integer conservation equations for atoms and charge, with positivity, gcd normalization and a declared minimality objective.", "No stoichiometric matrix, redox environment, species list or definition of minimality is supplied. An integer nullspace witness alone does not prove a minimum positive balance or impossibility.", [13,11], "Supply the finite species/charge matrix and objective; bind an exact integer witness plus infeasibility/minimality checker."),
106: ("Reaction-network deficiency n_complexes-linkage_classes-rank(S), graph linkage and weak reversibility, followed by theorem hypotheses on the chosen kinetics.", "No reaction graph or kinetic assumptions are supplied. Deficiency-zero/one conclusions cannot follow from the deficiency number alone.", [13,17], "Declare the network, stoichiometric matrix and kinetic regime, then check every theorem hypothesis separately."),
107: ("Finite group actions, orbit counts and Polya/Burnside-style enumeration under a declared stereochemical equivalence.", "No group action, molecular graph carrier, stereochemical identification or independent generator is present; an asserted count is not an enumeration certificate.", [13,17], "Provide the finite action and canonicalization rule and compare orbit counts with an independently owned generator."),
108: ("Flux-balance optimization as a rational linear program with primal and dual certificates and per-knockout feasibility tests.", "Stoichiometry, flux bounds, objective and lethality threshold are absent. A dual optimum for one LP says nothing about another knockout or biological validity.", [13,11,44], "Pin the stoichiometric LP and knockout transformations and check exact primal/dual or infeasibility witnesses for each."),
109: ("A declared finite kinetic network can support exact stationary probabilities, an error functional and a cost-constrained design comparison.", "The catalog provides no rates, transition generator, stationary-state uniqueness assumptions or thermodynamic cost definition; the biology analogy supplies none of them.", [13,11], "State the finite kinetic model, rates and cost/error predicates and produce independently checked steady-state witnesses."),
110: ("Fixed points and cycles of a finite Boolean transition system, with a completeness claim over the state graph.", "Update functions and synchronous/asynchronous semantics are absent; asynchronous attractors need a specified transition/scheduling interpretation, not simply synchronous cycles.", [13,17], "Freeze update functions and transition semantics; enumerate the declared carrier and certify every claimed terminal component."),
111: ("A finite HP lattice embedding can be checked for self-avoidance, contact energy and an announced energy bound.", "No chain, lattice, contact convention or bound is supplied. Checking one low-energy fold differs from proving its global optimality or inferring physical protein folding.", [13,44], "Supply the finite chain/lattice instance and exact contact predicate; distinguish feasible energy witnesses from optimality proofs."),
112: ("Fitch parsimony on a declared alignment and tree, with exhaustive/branch-and-bound evidence for a global optimum over a finite tree set.", "There is no alignment, alphabet, gap policy or tree-space definition. A per-tree Fitch score alone does not establish an optimal phylogeny.", [13,11], "Pin the alignment and search domain and require a complete bound/search certificate alongside the proposed tree."),
113: ("The next-generation matrix of a specified compartment model determines a spectral threshold, which may be decided by exact algebra under its stated sign assumptions.", "No matrices or compartment assumptions are supplied; rational entries do not imply a rational spectral radius, and a numerical eigenvalue is not an exact equality-to-one certificate.", [13,17], "Declare the next-generation construction and certify the sign of the threshold condition with explicit assumptions."),
114: ("Coverage and zero self-reactivity for r-contiguous detectors over explicitly finite string sets.", "No alphabet, r, self set or nonself carrier is provided. Perfect finite-panel coverage does not establish safety on unseen strings.", [13,14,41], "Pin the finite carrier and matching relation, and check both coverage and self-tolerance with collision/negative controls."),
115: ("Exact support/equilibrium equations and best-response inequalities for a nondegenerate rational bimatrix game, plus completeness over all supports.", "No payoff matrices or nondegeneracy witness are supplied. Verifying one Nash equilibrium is not enumerating all of them.", [13,11], "Declare the game and certify nondegeneracy, support enumeration coverage and all exact equilibrium inequalities."),
116: ("Fisher-market allocations and prices under a specified utility/budget model, with an Eisenberg-Gale/KKT optimality witness where its assumptions hold.", "The utility class, endowments, budgets and constraint qualifications are absent. KKT terminology alone is not an equilibrium certificate.", [13,11,44], "Specify the market model and exact primal/dual conditions before registering a certificate checker."),
117: ("Finite stable-matching feasibility with couples and ties, checked against a chosen blocking-pair/coalition definition.", "Weak, strong and super-stability differ; no preference instance or blocking convention is provided. Finding no blocking pair for one matching does not prove that no matching exists.", [13,17], "Freeze preferences, capacity and stability semantics and require a complete search/UNSAT witness for nonexistence."),
118: ("Discrete-type mechanism design as an explicitly encoded LP with incentive-compatibility, individual-rationality and primal/dual optimality witnesses.", "Type probabilities, utility model, allocation constraints and IC interpretation are absent. The abstract LP label cannot certify an auction's incentives.", [13,11,44], "Declare the finite type model and derive/check each IC/IR constraint and an exact optimum certificate."),
119: ("Kemeny aggregation minimizes a declared pairwise-disagreement objective over a finite ranking space.", "Votes, tie semantics, weights and optimum bounds are not present. A proposed ranking's score is not a proof that every alternative is worse.", [13,11], "Pin the voting profile/objective and require exhaustive coverage or an independently verifiable lower-bound certificate."),
120: ("Multiplicative consistency on a rate graph can be expressed by cycle products and vertex price potentials under explicit directed/reversible exchange semantics.", "The summary's cycle-product-not-one criterion requires qualification: a profitable directed cycle needs product greater than one, and reversing a losing cycle requires declared reverse edges/rates. Fees and direction cannot be omitted.", [13,10,17], "Define the directed rate model, fees and admissible reversals and distinguish inconsistency witnesses from profitable-cycle witnesses."),
121: ("Weighted-L1 reconciliation over a declared incidence/coboundary matrix, with dual circulation/obstruction and exact equality of primal and dual values.", "No ledger graph, sign convention, admissible edits or weights are supplied. The symbol H1 does not itself specify a ledger reconciliation problem.", [13,10,11,44], "Declare the ledger-to-cochain map and cost, then use the existing exact primal/dual certificate family."),
122: ("Exact Shapley sums and core feasibility for an explicitly finite characteristic-function game; balancedness/LP witnesses can decide the core under the declared formulation.", "No characteristic function, coalition bounds or payoff constraints are supplied. A few coalition checks do not establish all core inequalities.", [13,11], "Supply the full finite game and exact coalition-indexed constraints and separate value computation from core feasibility."),
123: ("Leontief productivity and output/price systems under declared nonnegative technology coefficients and Hawkins-Simon-type conditions.", "No coefficient matrix or sign/model assumptions are supplied; a matrix calculation without those assumptions is not an economic productivity conclusion.", [13,11], "Declare the input-output system and exact productivity criterion, then verify its conditions and solutions."),
124: ("Budgeted bandit allocation among model arms and a paired cost-to-certified-correct comparison against a uniform control.", "There is no reward stream, cost ledger or run. A dollar budget in a proposed plan is neither spent money nor authorization nor evidence of an adaptive advantage.", [22,37], "Specify a sealed task distribution, host reward/checker, budget accounting and paired uniform controls before considering execution."),
125: ("Negative selection of detectors against a finite self panel, followed by independent nonself detection evaluation.", "Self-tolerance is relative to the sealed panel; no actual detectors, antigens or negative controls are supplied here.", [14,41], "Bind a labeled public development panel and separate evaluation panel, recording both false positives and false negatives."),
126: ("A two-signal decision rule combines a pattern signal with independently justified structural evidence and compares error rates with a one-signal control.", "No detector or labeled corpus is supplied. Naming two signals neither establishes statistical independence nor measures prompt-injection or authority-laundering detection.", [14,41,39], "Define both evidence sources and the finite truth predicate and evaluate collision, benign and adversarial controls before admission."),
127: ("Budgeted clonal mutation/selection of detectors can be tested for held-out coverage gains while preserving self-tolerance.", "No mutation operator, antigen carrier, objective or measured transfer is present; selection on development items cannot establish hidden-family generalization.", [14,19,41], "Freeze mutation and selection rules and evaluate each candidate on disjoint variant families with self-panel controls."),
128: ("Treg-style suppression is a detector-control policy whose false-positive reductions and false-negative costs must be measured jointly.", "There is no controller or detector panel. Suppressing repeated alerts does not prove that danger coverage is preserved.", [14,41], "Specify suppression state/transitions and compare coverage and false alarms before and after suppression on a fixed panel."),
129: ("Delayed rechecking may trade error rate against token/time cost under a specified sequential acceptance policy.", "No timing rule, fresh evidence or cost/error data is supplied. Repeating a correlated check is not independent verification or a kinetic theorem.", [9,14,22], "Declare stopping/retraction rules, checker independence and matched cost controls and measure the actual error/cost tradeoff."),
130: ("A Hill-style quorum is a proposed nonlinear aggregation rule over several model scores, compared with a single model and simple majority.", "No calibrated scores, aggregation parameters or host truth labels are supplied. Model agreement is not a mathematical certificate.", [4,41,22], "Pin the aggregation function and calibration set and evaluate against a host checker with matched single/majority controls."),
131: ("Partial observations require an explicit global failure predicate and a sufficient handoff/gluing relation between local reports.", "No observation cover or global instance is supplied. Local acceptance cannot imply global correctness without a proved or checked sufficiency condition.", [4,10,46], "Declare each view, the handoff object and global evaluator, then test locally accepted but globally defective controls."),
132: ("A complement-style escalation policy can recruit verifiers under a finite resource budget and explicit activation/regulation transitions.", "No executable cascade, budget invariant or measured detection is present; a proposed escalation cannot establish bounded cost by its name.", [9,14,41], "Supply the state machine and resource accounting and check both missed-danger and runaway-escalation controls."),
133: ("Failure-derived operand retrieval can be compared with a baseline for held-out accuracy and second-exposure cost.", "The half-cost goal is unmeasured. No corpus, retrieval rule or matched variant-family experiment is present.", [3,19,22], "Freeze the mined rule corpus and split, then measure certified accuracy and billed/tool cost with a retrieval-disabled control."),
134: ("Adversarial example mining can enlarge a finite judge mutation panel if provenance and development/evaluation separation are maintained.", "No generated adversaries, execution or mutation results exist here. Adaptive examples can contaminate a supposedly held-out panel.", [14,19,29,48], "Register the mutation grammar and custody/split rules, then score every new adversary through the existing host checker."),
135: ("Validity, inconsistency and modal collapse can be investigated in explicitly encoded modal systems with proof objects or finite countermodels.", "The capsule supplies named ontological arguments but no translations, axioms or semantics. A formal result is conditional on those encodings and does not establish a theological proposition.", [15,17], "Pin each modal translation and frame/axiom assumptions and require a proof or countermodel for the exact statement."),
136: ("Absolute/relative-identity and constitution theories can be compared using finite-model witnesses or unsatisfiability certificates for declared axioms.", "There is no formal identity theory or domain bound here. A finite model is a consistency witness for its encoded sentences, not a verdict on religious truth.", [15,17], "Declare each equality/identity language and axiom set, preserving non-equivalent translations as separate cases."),
137: ("Minimal inconsistent and maximal satisfiable subsets of an explicitly formalized attribute theory can be checked with exact witnesses.", "The capsule gives no axiom translations or logic. An unsat core is not necessarily minimal; finite satisfiability does not settle informal divine-attribute compatibility.", [15,17], "Freeze the logic and axioms and validate every minimality/satisfiability claim against an independent checker."),
138: ("Deontic paradox encodings admit conditional consistency, independence and redundancy tests in a declared logic.", "There is no normative interpretation or formal axiom set. Translation choices determine what is tested; a syntactic result does not resolve an informal paradox by itself.", [15,17], "Supply explicit Chisholm/Ross translations and distinguish models, countermodels and independence witnesses."),
139: ("Grounded, preferred, stable and semi-stable extensions of a finite Dung attack graph are distinct exactly checkable semantics.", "The attack graph and extension definitions are not supplied. Enumerating one semantics does not certify another or establish the truth of accepted arguments.", [15,13], "Pin the graph and each semantic predicate and verify complete extension sets separately."),
140: ("Toy diagonal fixed points and quines require explicit syntax, quotation/substitution and evaluation relations.", "No language or interpreter is supplied. A self-reproducing string is not a general incompleteness result or an ontological derivation.", [16,17], "Declare the encoding and evaluator and check the exact fixed-point equation with malformed/near-quine controls."),
141: ("Finite truth-value assignments for K3, LP or FDE can be checked against their specified designated values and fixed-point constraints.", "The systems differ, and no truth tables, implication/connective choices or encoded liar/Curry/Yablo instances are given. A finite Yablo truncation is not the infinite construction.", [15,17], "Freeze each logic and finite instance and verify its valuations without pooling incompatible semantics."),
142: ("A cut-elimination transformation for LK/LJ should preserve the exact end sequent and produce a cut-free proof, with explicit size accounting.", "No calculus, proof object or transformation is present. One normalized proof is not a general cut-elimination theorem.", [16,17,44], "Provide the proof grammar and rule checker and validate end-sequent preservation, cut absence and measured output size."),
143: ("A k-round Ehrenfeucht-Fraisse game admits a bounded distinguishing formula or a checked Duplicator strategy for a declared vocabulary and finite structures.", "No structures, vocabulary or k are supplied. Bounded game equivalence does not establish unrestricted elementary equivalence.", [17,13], "Pin the structures and round bound and validate a complete strategy tree or bounded-rank formula witness."),
144: ("An AuthorityEffect=None invariant can be proved by induction over a declared transition relation and its composition rules.", "No Lean definitions or transition owner are supplied in the capsule. A status string alone is not an invariant, and the theorem applies only to modeled paths.", [39,16], "Bind the actual routing/gate transition semantics and prove preservation for every allowed constructor and composition."),
145: ("Recovered G01 specifies pinned core-Lean statements F-1, F-5 and F-K for non-isomorphic item-count minima of reading F; proof types and axiom reports must be checked.", "The recovered spec is a planned target, not a proof. At least five classes differs from exactly five; finite enumeration does not prove the k-ary family or choose a reading or tied class.", [16,17,45], "Preserve the recovered specification and resolve its external sealed definitions/pins before compiling statement-pinned proofs in a separate authorized study."),
146: ("Recovered G02 specifies a list-filter cut census with distinct in-range designated points and the general 2^(n-2) theorem, separate from finite carrier checks.", "The planned proof depends on exact definitions and n>=2/distinctness/range hypotheses. Counting carriers 5–8 does not prove the universal formula or confer an external meaning on cuts.", [16,17], "Resolve the sealed definitions and verify exact theorem types, edge cases and axiom reports; keep census and general proof statuses separate."),
147: ("Recovered G03 requires an injective collapse-preserving chain-to-regime adapter, per-pair min_responses call arguments and class-based weak/strong predicates on 455 declared pairs.", "The adapter is new declared structure. A loop count without argument provenance can repeat fixed targets; even a complete replay establishes only this finite adapter, not general G4 or demand generation.", [18,16,17,42], "Preserve the call-argument instrumentation and fixed-target negative control requirements; resolve the external engine and adapter before any replay."),
148: ("Recovered G04 separates token renaming, prefix-wise isomorphism with transported stakes, and fixed-stake invariance, with finite history witnesses.", "Endpoint class alone is explicitly recorded as insufficient. A rectangle result is bounded, and absence of a nontrivial isomorphism would give a vacuous case rather than automatically making invariance ill-posed.", [17,16], "Freeze the precise reading and stake transport, resolve the external history engine and replay both positive and counterexample controls."),
149: ("Recovered G05 requires a sound and complete finite context enumeration, constructive decidability of HasDemand, and the first-count theorem with the decidability premise discharged.", "Removing the decidability premise does not remove the premise that some prefix actually carries a demand. The proposed Lean result supplies no endogenous demand generator.", [16,17], "Resolve the pinned kernel and prove slot-list completeness and exact statement preservation; retain the demand-existence hypothesis in all summaries."),
150: ("Recovered G06 distinguishes a finite commuting-square census from the universal Closed(writes) statement for one pinned transition system, proved or refuted in Lean.", "Its 240/952-state and square counts are historical assertions not replayed here. A larger zero-boundary census is not a general theorem, physical conservation law or unqualified cohomological claim.", [10,16,17], "Resolve the state/event semantics, reproduce the historical census independently and require a theorem or explicit commuting-square counterexample for the universal claim."),
151: ("Recovered G07 counts canonical minimum-response classes by depth for fixed Bounds(2,2), populations and supply policy, while leaving a quantified fan-width conjecture OPEN.", "Raw delta counts differ from quotient widths. Finite depths and a single trajectory cannot prove boundedness or unboundedness, and a unique minimum does not authorize application.", [17,18,45], "Resolve the pinned populations and canonicalizer, reconcile finite counts and label any general bound as conjectural until separately proved."),
152: ("Recovered G08 specifies fault injection into a pinned temporary copy, observing the named failure and restored pass for coverage and Lean-axiom/report gates.", "A synthetic parser fixture is not a live compiled-path injection; successful finite injections still do not prove all defects detectable or any driver-refinement theorem.", [29,41,42], "Preserve the exact failure/reversal/custody contract; resolve the external Alpha Engine snapshot and test liveness on copies only in a separately authorized execution phase."),
}

manifest_path = ROOT / "dag/migrations/anomalon_pilots_move.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
custody = {"pilots/anomalon_woland/" + row["path"]: row for row in manifest["entries"]}
reads_path = PREFIX.with_name(PREFIX.name + "_reads.json")
reads = json.loads(reads_path.read_text(encoding="utf-8"))
assert len(reads) == 612 and len({row["path"] for row in reads}) == 612
citations = {x["pilot"]: x for x in json.loads(PREFIX.with_name(PREFIX.name + "_citation_resolution.json").read_text(encoding="utf-8"))}

def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()

def evidence(path, level="full_source_read_and_substantively_reviewed", lines=None, assessment=None):
    raw = (ROOT / path).read_bytes()
    count = raw.count(b"\n") + int(bool(raw) and not raw.endswith(b"\n"))
    row = {"path": path, "sha256": hashlib.sha256(raw).hexdigest(), "lines": lines or [1, count], "review_level": level}
    if path in custody:
        c = custody[path]
        assert row["sha256"] == c["sha256"]
        row.update(source_git_tracked=c["source_git_tracked"], source_git_blob=c["source_git_blob"])
    if assessment:
        row["assessment"] = assessment
    return row

FUNCTION_ASSESSMENT = {
"README.md": "Full claim-hygiene and provenance declaration: planned catalog capsule, no dispatch, no current checker binding and no fresh success claim.",
"seed.yaml": "Public catalog title/summary/citation and a PLANNED expected status; this contains no mathematical instance or protected QM benchmark seed.",
"spec.yaml": "Layout coordinates and a synthetic checker id; exact_modular/answerable/cochain_norm are declarations, not verified contracts or measurements.",
"prompt_template.yaml": "Full shared glyph/operator/SPK and witness-first prompt; generic response schema and claim hygiene do not implement the domain predicate.",
"testplan.yaml": "One planned catalog-summary case; repeated prompt/layout fields supply no mathematical test execution.",
"tests/test_00/input.yaml": "Complete generated public prompt matches the planned template; no concrete domain instance or mathematical oracle is injected.",
"tests/test_00/response.yaml": "NOT_RUN with null reply/reasoning/parsed payload and empty metrics; no empirical result.",
"tests/test_00/test_spec.yaml": "Planned test coordinates and source description; not an executable test/checker.",
"misc/README.md": "Aggregate-file explanation and planned-only status; no learned operands or live trace.",
"misc/comparison_results.md": "No comparison has been executed; no accuracy or efficacy evidence.",
"misc/comparison_results.yaml": "Empty tests array and null aggregate metrics; total_tests is a planned count, not a completed trial.",
"misc/cot_mine.yaml": "Trace count zero, skipped response and empty mined patterns; historic miner-command success establishes no learning or dispatch.",
}

for row in reads:
    path = ROOT / row["path"]
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == row["sha256"] == custody[row["path"]]["sha256"]
    assert row["lines"] == [1, raw.count(b"\n") + int(bool(raw) and not raw.endswith(b"\n"))]
    number = int(path.relative_to(BASE).parts[0].split("_")[1])
    rel = path.relative_to(BASE / f"pilot_{number:07d}").as_posix()
    pairs = row["simultaneous_exact_replacements"]
    template = (ROOT / row["template_path"]).read_bytes().decode("utf-8")
    if pairs:
        pattern = re.compile("|".join(re.escape(k) for k in sorted(pairs, key=len, reverse=True)))
        template = pattern.sub(lambda match: pairs[match.group(0)], template)
    delta = list(difflib.unified_diff(template.splitlines(keepends=True), raw.decode("utf-8").splitlines(keepends=True),
                                    fromfile="mapped_template/" + rel, tofile=f"pilot_{number:07d}/" + rel, n=2))
    assert delta == row["residual_diff"]
    row["review_level"] = "full_source_read_baseline_plus_all_exact_replacements_and_residual_differences"
    row["full_source_read"] = True
    row["assessment"] = FUNCTION_ASSESSMENT[rel]
reads_path.write_text(json.dumps(reads, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

registry_path = "dag/workflows_dag.json"
registry_text = (ROOT / registry_path).read_text(encoding="utf-8")
registry = json.loads(registry_text)
node_by_id = {node["id"]: node for node in registry["nodes"]}
# Exact physical line spans of selected node objects, without emitting benchmark fields.
pos = registry_text.index("[", registry_text.index('"nodes"')) + 1
decoder = json.JSONDecoder()
node_spans = {}
while True:
    while registry_text[pos] in " \r\n\t,":
        pos += 1
    if registry_text[pos] == "]":
        break
    node, end = decoder.raw_decode(registry_text, pos)
    node_spans[node["id"]] = [registry_text.count("\n", 0, pos) + 1, registry_text.count("\n", 0, end) + 1]
    pos = end

P58 = "workflows/tasks/certified_challenges/c058_straight_line_superoptimization/"
P59 = "workflows/tasks/certified_challenges/c059_sql_null_total_query_synthesis/"
P60 = "workflows/tasks/certified_challenges/c060_self_verifying_checker_synthesis/"
OWNERS = {
102: [P58 + p for p in ["CHALLENGE.md", "participant_packet/TASK.md", "judge_packet/exact_checker.py", "judge_packet/evaluator.py", "judge_packet/independent_checker.py", "reference_solver/superoptimizer.py", "reference_solver/solver.py", "tests/test_c058_unknown_and_trivial_responders.py"]],
103: [P59 + p for p in ["participant_packet/TASK.md", "judge_packet/exact_checker.py", "judge_packet/independent_checker.py", "judge_packet/relational_interpreter.py", "judge_packet/sqlite_relational_oracle.py", "relational_contract.py", "sqlite_read_boundary.py", "reference_solver/compiler.py", "reference_solver/solver.py", "tests/test_contract_ownership.py", "tests/test_independent_judge_ownership.py"]] + ["pilots/anomalon_woland/c059_sql_null_total_query_synthesis/docs/c059_sql_null_total_query_synthesis.md"],
104: [P60 + p for p in ["participant_packet/TASK.md", "judge_packet/exact_checker.py", "judge_packet/independent_checker.py", "reference_solver/checker.py", "participant_packet/runner.py", "tests/test_c060_unknown_and_trivial_responders.py"]],
}
recovery = "papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/docs/history_recovery/recovered_sources/"
for n in range(145, 153):
    OWNERS[n] = [recovery + info(n)["source_markdown"].split("/")[-1]]

def related_assessment(n, path):
    if n >= 145:
        return "Full recovered historical planned specification read, including exact targets, public-example/test plans, judge controls and claim limits. External 19L57G1 implementations and historical outcomes were not accessed or replayed. " + ASSESS[n][1]
    if "/tests/" in path:
        return "Complete test source read, not imported or executed. Fixture loading would read external judge cases, so no suite run was made; source assertions are intended coverage, not fresh results."
    if path.endswith("CHALLENGE.md") or path.endswith("TASK.md") or "/docs/" in path:
        return "Complete domain specification read; historical/planned execution statements separated from the current owner. " + ASSESS[n][1]
    return "Complete owning implementation read, including contracts and failure paths. " + ASSESS[n][0] + " Limit: " + ASSESS[n][1]

external_reviews = [evidence(path, assessment=related_assessment(n, path)) for n, paths in OWNERS.items() for path in paths]
for e in external_reviews:
    e["full_source_read"] = True

pilots = []
for n in range(102, 153):
    meta = info(n)
    basis, limit, families, action = ASSESS[n]
    local = [row for row in reads if row["path"].startswith("pilots/anomalon_woland/" + meta["pilot_id"] + "/")]
    assert len(local) == 12
    src = [{k: row[k] for k in ("path", "sha256", "lines", "review_level", "full_source_read", "source_git_tracked", "source_git_blob", "assessment")} for row in local]
    src += [e for e in external_reviews if e["path"] in OWNERS.get(n, [])]
    mappings = []
    for f in families:
        fid = "WF" + str(f)
        node = node_by_id[fid]
        mappings.append({"family_id": fid, "path": node["path"], "registry_status": node["status"],
                         "registry_source_evidence": evidence(registry_path, "selected_existing_family_node_process_math_sources_read", node_spans[fid]),
                         "relationship": "Existing canonical family comparison for this proposed domain task; no new family and no evidence that this numbered capsule executes the family. " + ("Domain-checker registration precedes dispatch." if f == 13 else "Reuse requires the declared mathematical carrier, owner and interface; the mapping is conceptual, not a runtime binding.")})
    verdict = "duplicate_candidate" if n <= 104 else "stub_candidate"
    contribution = ("Planned catalog alias to an existing C0" + str(n - 44) + " domain owner: " if n <= 104 else "Planned catalog task capsule: ") + meta["title"] + ". " + meta["summary"]
    p = {"id": meta["pilot_id"], "path": "pilots/anomalon_woland/" + meta["pilot_id"],
         "catalog_id": meta["catalog_id"], "contribution": contribution,
         "mathematical_basis": basis, "reusable_mechanism_name": ("existing_domain_owner_alias_" if n <= 104 else "planned_domain_capsule_") + meta["catalog_id"].lower(),
         "qm_seed_transfer": {"protected_qm_seed_read": False, "mathematical_support_for_unchanged_qm_seed": "NOT_ESTABLISHED", "requires_seed_appropriate_checker_or_encoding": True,
             "prerequisite": "Declare and independently check the target task's encoding, mathematical predicate/certificate and negative controls. This domain-specific planned capsule does not establish transfer to an unspecified QM task.",
             "reusable_without_claiming_qm_correctness": "Custody, typed abstention, proposal/checker separation, statement pins or replay controls may transfer after interface matching; that is not a mathematical or physical derivation."},
         "actual_execution_status": {"audit_model_calls": 0, "audit_full_test_suite_run": False,
             "historical_catalog_status": meta["historical_catalog_status"], "historical_status_is_fresh_execution_evidence": False,
             "response_schema_census": {"response_count": 1, "statuses": {"NOT_RUN": 1}, "nonempty_raw_reply_count": 0},
             "test_sources_present": [], "mechanism_execution": "No executable source in this capsule; one planned test layout, no dispatched model, no nonnull reply, no learned trace and no metrics.",
             "ceiling": "The external owner/specification is separately evidenced where found; it supplies no retroactive execution of this capsule.",
             "current_smoke_probe": ("dag/pilot_triage/numbered_102_152_probe_results.json" if n <= 104 else None)},
         "source_evidence": src, "citation_resolution": citations[meta["pilot_id"]],
         "workflow_mapping": mappings, "verdict": verdict,
         "rationale": ("This is a catalog/provenance wrapper around an existing domain implementation, not a second independent mechanism; duplicate_candidate means an alias/consolidation candidate, not byte identity or deletion permission. " if n <= 104 else "The numbered directory is a planned stub with no domain instance, executable checker or experiment. Preserve its planning/provenance value. ") + limit,
         "mathematical_limits": limit, "next_action": action}
    p["citation_resolution"]["direct_legacy_path_present_after_prefix_mapping"] = (BASE / meta["source_markdown"].removeprefix("omega_engine_education/pilots/")).exists()
    p["citation_resolution"]["historical_spec_file_present_recorded"] = meta["spec_file_present_recorded"]
    p["citation_resolution"]["external_owner_or_recovered_spec_read"] = OWNERS.get(n, [])
    pilots.append(p)

probe_path = "dag/pilot_triage/numbered_102_152_probe_results.json"
probes = json.loads((ROOT / probe_path).read_text(encoding="utf-8"))
assert len(probes["results"]) == 6

findings = [
 {"id": "P102-152-PLANNED-ONLY", "severity": "evidence_boundary", "claim": "All 51 numbered entries are planned wrappers, not executed mechanisms or empirical successes.", "evidence": [evidence("pilots/anomalon_woland/pilot_0000102/README.md", lines=[10,39]), evidence("pilots/anomalon_woland/pilot_0000102/tests/test_00/response.yaml"), {"path": "dag/pilot_triage/numbered_102_152_reads.json", "sha256": sha("dag/pilot_triage/numbered_102_152_reads.json"), "scope": "all 612 files"}], "limit": "This does not say the mathematical tasks are trivial or that no implementation exists elsewhere."},
 {"id": "P102-152-LOCATORS", "severity": "integration_backlog", "claim": "All 51 original legacy source paths are absent at the directly mapped imported location. Same-filename recovery finds C059 and G01–G08; canonical C058/C060 owners have different filenames.", "evidence": [evidence("dag/pilot_triage/numbered_102_152_citation_resolution.json", "generated_filename_inventory_checked")], "limit": "No same-filename match for C061–C100 is not proof of global absence under renamed files or external repositories. No locator was rewritten."},
 {"id": "P102-C058-SAMPLED-CERTIFICATE", "severity": "high", "claim": "Both C058 checkers accept a width-32 candidate that is inequivalent at x=42; larger-width sampling does not implement the proof-certified equivalence contract.", "evidence": [evidence(P58 + "CHALLENGE.md"), evidence(P58 + "judge_packet/evaluator.py", lines=[172,264]), evidence(P58 + "judge_packet/independent_checker.py", lines=[262,314]), evidence(probe_path, "fresh_public_toy_probe_result")], "limit": "One explicit false acceptance refutes universal acceptance soundness for this path; it does not estimate the historical error rate or invalidate width-8 exhaustive checking."},
 {"id": "P103-C059-TYPE-SEMANTICS", "severity": "high", "claim": "C059's two owners disagree on an admitted TEXT column containing '1' compared with integer literal 1: SQLite affinity accepts the row, Python equality drops it.", "evidence": [evidence(P59 + "judge_packet/sqlite_relational_oracle.py"), evidence(P59 + "judge_packet/relational_interpreter.py", lines=[49,63]), evidence(P59 + "relational_contract.py"), evidence(probe_path, "fresh_public_toy_probe_result")], "limit": "The probe shows an unresolved coercion/typing contract, not that either checker is always wrong. Stop-on-disagreement can detect it; no stored matrix or historical provider run was replayed."},
 {"id": "P104-C060-CONTRACT-BOUNDARIES", "severity": "high", "claim": "Both C060 mathematical implementations accept n=0 despite the participant contract; the reference accepts a trailing newline in a rational string, the owners disagree on non-string value rejection code, and the independent parser raises ValueError on a Unicode digit.", "evidence": [evidence(P60 + "participant_packet/TASK.md"), evidence(P60 + "reference_solver/checker.py"), evidence(P60 + "judge_packet/independent_checker.py"), evidence(probe_path, "fresh_public_toy_probe_result")], "limit": "These are schema/totality/contract failures, not a counterexample to weak duality under valid dimensions and canonical rational inputs."},
 {"id": "P104-C060-SCORER-CUSTODY", "severity": "evidence_boundary", "claim": "The C060 first checker scores against expected_verdict/expected_code fields rather than deriving mathematical ground truth; the separate independent checker is necessary for algebraic validation.", "evidence": [evidence(P60 + "judge_packet/exact_checker.py")], "limit": "Correct fixture labels can make this a useful scorer, but the scorer alone cannot authenticate its labels or prove universal candidate-checker correctness."},
 {"id": "WF29-TERMINOLOGY", "severity": "documentation", "claim": "WF29's phrase 'soundness requires zero false rejections' conflates valid-input acceptance with invalid-input rejection. Both finite error directions matter, and neither panel alone proves universal soundness/completeness.", "evidence": [evidence("workflows/wf29_checker_synthesis_scored_by_mutation_kill_rate/README.md")], "limit": "A registry wording concern only; historical live-score prose was not authenticated in this triage."},
 {"id": "P145-152-RECOVERED-PLAN-BOUNDARY", "severity": "evidence_boundary", "claim": "Recovered G01–G08 documents contain substantive target statements, proposed public examples and judge plans, but not the requested proofs, executable adapters or live injection receipts.", "evidence": [e for e in external_reviews if e["path"].startswith(recovery)], "limit": "External 19L57G1 pins and historical counts remain unverified; no derivation of physical QM, endogenous demand, reading selection or authority follows from these planned contracts."},
]

report = {"schema": "pfp.imported-pilot-triage.v1", "source_commit": PIN,
 "scope": "All 51 imported numbered directories pilot_0000102 through pilot_0000152 inclusive; all 612 local files fully read using a full baseline and lossless full differences; separately listed shared owners and recovered specifications also read.",
 "status": "complete_first_substantive_triage_not_full_estate_certification",
 "authority_effect": "None; recommendations only. No imported/source file edited or deleted and no provider/model call made.",
 "summary": {"pilot_count": 51, "local_file_count": 612, "local_full_source_reads": 612, "local_executable_source_count": 0,
             "local_physical_lines_reviewed": sum(r["lines"][1] for r in reads), "related_full_source_files_read": len(external_reviews),
             "verdict_counts": dict(Counter(p["verdict"] for p in pilots)), "new_workflow_families_recommended": 0,
             "fresh_public_toy_probes": 6, "planned_not_run_capsules": 51, "recovered_genesis_specs_read": 8},
 "review_method": [
   "Read all 12 pilot_0000102 files in full. For every other pilot, read every literal simultaneous replacement and every residual difference against that baseline; independent ndiff restoration and final exact-diff/hash checks preserve the whole source, not merely parsed fields.",
   "All 51 capsule metadata/claims were assessed individually. Physical line spans, SHA-256 and migration source tracked/blob custody accompany every local file. The read ledger preserves exact template hashes, replacements and residual diffs.",
   "Read the complete recovered G01–G08 primary specifications and the specifically listed C058/C059/C060 contracts, owning evaluators/checkers/proposers and selected complete test sources. This is not an exhaustive review of those external packages.",
   "Compared the 49 existing workflow-family node process/math/source fields; selected node spans are cited. Full WF13/WF29 READMEs were also read. Generated combinations do not count as new families.",
   "Six fresh public toy probes used only in-memory cases constructed in this audit and owner functions, with bytecode disabled; no historical case files, provider dispatch or full suites were run.",
   "Filename-only citation resolution used Git-tracked paths plus migration-manifest paths. Source absence is bounded to that search, not asserted across external repositories or renamed files."
 ],
 "evidence_limits": [
   "PLANNED expected answers, 8B model-class labels, difficulty 2, target_spend_usd 0, exact_modular, cochain_norm and synthetic checker ids are layout declarations, not accuracy/cost/difficulty/calibration measurements or runtime bindings.",
   "The shared generic JSON answer envelope has no domain semantics. Prompt guidance, SPK/operator licensing and an intermediate-witness request cannot substitute for a registered mathematical checker.",
   "C058/C059/C060 external owners are separate artifacts; locating them does not turn these numbered wrappers into executed experiments. Historical completed/scored/live claims were not independently reproduced.",
   "Recovered Genesis specs retain their planned status. External 19L57G1 theorem source, axiom reports, sealed definitions, historic counts and receipts were not accessed or certified here.",
   "Related-package example directories, hidden fixture/generator data, entire suites and unlisted modules are outside the complete local-file coverage claim. Selected tests were read, not imported; their top-level fixture reads were not executed.",
   "No protected QM seed, private benchmark storage or answer key was read; no benchmark was solved. Public capsule seed.yaml files contain catalog summaries only.",
   "No external literature/novelty search was performed; mathematical statements are conditional source-contract analyses. Reuse recommendations are local registry mappings, not proof of scientific novelty or efficacy."
 ],
 "context_evidence": [evidence("pilots/anomalon_woland/README.md"), evidence("pilots/anomalon_woland/MODUS_OPERANDI.md"), evidence("workflows/wf13_exact_domain_capsule_battery/README.md"), evidence("workflows/wf29_checker_synthesis_scored_by_mutation_kill_rate/README.md")],
 "registry_evidence": {"path": registry_path, "sha256": sha(registry_path), "review_scope": "49 existing workflow family nodes, selected process/math/source fields; benchmark contents not used."},
 "custody": {"manifest": "dag/migrations/anomalon_pilots_move.json", "manifest_sha256": sha("dag/migrations/anomalon_pilots_move.json"), "source_repository_commit": manifest.get("source_commit"), "all_612_bytes_match_manifest": True},
 "findings": findings, "related_file_reviews": external_reviews, "pilots": pilots,
 "validation": {"local_files_checked": 612, "complete_pilot_id_set": True, "local_manifest_hash_matches": 612, "all_lossless_residual_diffs_revalidated": True,
                "full_test_suite_run": False, "model_calls": 0, "probe_results": probe_path, "probe_status": probes["status"], "python": probes["python"]},
 "supporting_artifacts": ["dag/pilot_triage/numbered_102_152_reads.json", "dag/pilot_triage/numbered_102_152_citation_resolution.json", probe_path, "dag/pilot_triage/numbered_102_152_probes.py"],
 "remaining_work": ["No unread files remain within these 51 numbered capsule directories.", "Repair recommendations are backlog only; external owner contract defects are not fixed.", "Deep complete coverage of external shared packages, historic results and external Genesis repositories is not claimed.", "The broader every-file repository audit remains a separate active objective; this triage completes only the assigned 51-pilot slice."]}
assert {p["id"] for p in pilots} == {f"pilot_{n:07d}" for n in range(102, 153)}
required = {"id", "path", "contribution", "mathematical_basis", "reusable_mechanism_name", "qm_seed_transfer", "source_evidence", "workflow_mapping", "verdict", "rationale", "next_action"}
assert all(required <= p.keys() for p in pilots)
PREFIX.with_suffix(".json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

md = ["# Imported pilots 102–152: substantive triage", "",
      "All **51 pilots / 612 local files** were read. The capsules are **PLANNED / NOT_RUN**: no local executable checker, dispatched reply, learned trace or measured result. The full baseline plus every literal replacement and residual difference is preserved in the read ledger and every local hash matches the migration manifest.", "",
      "Verdicts: **3 duplicate candidates** (catalog aliases to C058–C060 owners) and **48 stub candidates**. These labels recommend preserving provenance and consolidating registration; they authorize no deletion. No new workflow family is needed.", "",
      "Eight recovered G01–G08 specifications and the listed C058–C060 owners were read separately. Their mathematical contracts have value, but they supply no retroactive execution of the numbered capsules.", "",
      "Six public toy probes reproduced three owner concerns: C058 accepts a wrong width-32 program through both sampled checkers (at x=42, original 0, candidate 1); C059 judges disagree on TEXT/integer affinity; C060 has zero-column, canonical-string, rejection-code and totality defects. Full cases and outputs are in numbered_102_152_probe_results.json. These results establish those bounded defects, not historical error rates.", "",
      "The recovered Genesis plans carefully distinguish finite census, statement-pinned Lean proof, adapters and live defect injections. No external proof/build/count was replayed. G05 still assumes a prefix carrying demand after constructive decidability is supplied. None of these plans chooses a reading, generates endogenous demand, grants authority or supports an unchanged QM seed.", "",
      "No protected benchmark seed, private storage or answer key was read. No model/provider calls, source edits, pilot edits or quality deletions occurred. Source comparison is pinned to `" + PIN + "`; imported custody uses the migration manifest.", "",
      "| Pilot | Catalog | Verdict | Existing families | Next action |", "|---|---|---|---|---|"]
for p in pilots:
    md.append("| " + " | ".join([p["id"], p["catalog_id"], p["verdict"], ", ".join(x["family_id"] for x in p["workflow_mapping"]), p["next_action"].replace("|", "/")]) + " |")
md += ["", "The JSON report contains each pilot's distinct mathematical basis, limitations, exact source hashes/ranges, custody and workflow mapping. The 612-file ledger records full-source review method and per-file assessment. Related external packages are reviewed only to the explicitly listed extent; this completes the assigned pilot slice, not the whole repository audit."]
PREFIX.with_suffix(".md").write_text("\n".join(md) + "\n", encoding="utf-8")
print(json.dumps({"status": report["status"], "summary": report["summary"], "output": str(PREFIX.with_suffix('.json'))}, indent=2))
