# Workflow-DAG wiki review

Completed the frozen one-file scope: **1,669 lines, 78,366 bytes, 49 families and 46 perturbations**. Every line was read; no original source was changed. SHA-256: `8ea5f483e55afe7fbb29b298633a38d6eb7d11349c43b862d14972841ba0ee33`.

The page usefully distinguishes five implemented finite-task runners from 44 proposed families. Its 75 design edges agree with the registry and prose and form a DAG. All 55 repository link targets exist locally. These checks establish catalog consistency, not executable composition, checker soundness or model efficacy.

The review retains the useful mechanisms: typed task boundaries, exact domain predicates, checked representation maps, claim-scoped receipts, shared fuel, custody, replay and properly held-out comparisons. Domain presets and named roles are not new general mathematical foundations.

## Findings

### WIKI-WFD-F01 — WF44 certificate formula admits a nonoptimal result

For the oriented triangle B, w=(2,2,2), f=(0,3,5), z=(2,2,2), the page conditions give r=(5,4,-3), B^T z=0, |z|<=w and w.z=||r||1=12. Yet f=0 gives norm 6, which is optimal because sum(r)=6 for every f. The displayed rule is not a valid unweighted optimality certificate.

**Action:** Separate signed cochain c from positive weights alpha. Unweighted: r=c+Bf, B^Tz=0, |z|<=1, c.z=||r||1. Weighted: |z|<=alpha and c.z=sum(alpha_e|r_e|).

**Wiki evidence:** L1457–1468.

**Prior relationship:** papers_audit PFP021 workflow-math; this is a corroborated wiki occurrence with a new exact finite counterexample.

### WIKI-WFD-F02 — Non-derivability is not the right leakage contract

WF23 requires that no expected answer be derivable or a declared function of participant bytes. A deterministic task such as public 2+3 is legitimately solved by a declared function of those bytes. WF43 similarly needs to distinguish solved acceptance from a legitimate answer-free typed refusal. Existing packet audit is bounded lint/probing, not a general information-flow proof.

**Action:** Specify prohibited disclosure and judge access rather than mathematical non-derivability; separate solved, justified-refusal and transport statuses. Keep leakage lint as a bounded diagnostic.

**Wiki evidence:** L854–868, L1429–1443, L354–374.

**Prior relationship:** papers_audit PFP021 workflow-math; shared_runtime judge_packet_audit

### WIKI-WFD-F03 — WF29 reverses soundness and completeness

Zero false rejections concerns completeness, while soundness says accepted outputs are valid. A reject-all checker is sound in this acceptance sense but incomplete on a nonempty valid set. Killing all listed mutants and accepting all listed valid cases remains finite-panel evidence, not either universal property.

**Action:** Use false acceptance/soundness and false rejection/completeness terminology and state the exact finite panel and mutation operators.

**Wiki evidence:** L1027–1041.

**Prior relationship:** papers_audit PFP021 workflow-math

### WIKI-WFD-F04 — Historical totals repeat withdrawn or overgeneralized source claims

WF27 labels 28 trials live although the corrected owner review retains eight supplied one-fixture traces; full-repair hints are appropriately disclosed but do not repair the count. WF48 universal 64/64 and 48/48 self-scores overgeneralize the narrower source accounts: the earlier workflow audit explicitly records the C049 secondary checker accepting 31/48 mutants. New counterexamples elsewhere do not themselves disprove an old finite score; they limit the soundness inference from that score. The blanket table errata notice does not identify which row is withdrawn.

**Action:** Bind each numerical row to a specific retained report edition, population and checker; mark withdrawn totals at the row itself. Keep model replies, self-scores, finite source probes and historical counts separate.

**Wiki evidence:** L970–983, L1569–1584, L1620–1669.

**Prior relationship:** papers_audit PFP021 withdrawn-counts; additional_paper_008_support PAPER008-HISTORICAL-MODEL-CLAIM-CEILING; additional_paper_010_support and challenge reviews. No historical call was reauthenticated.

### WIKI-WFD-F05 — WF27 lag-three recurrence is not stationarity

The formula r_t=r_(t-3) also holds for the periodic sequence 1,2,3,1. It does not establish three repeated unchanged residuals or a stationary loop. Periodicity may still justify a separately declared cycle policy.

**Action:** If stationarity is intended require consecutive equality; otherwise name and record the detected cycle and check that any forced lift preserves the task.

**Wiki evidence:** L974–985.

### WIKI-WFD-F06 — WF41 representative completeness omits its invariance premise

D=A on one representative per class implies D=A everywhere only when both functions factor through those classes. On one class {0,1}, R={0}, A=(false,false), D=(false,true), representative agreement holds but global agreement fails. The n=299 zero-failure bound is valid only with a stated confidence level and independent sampling assumptions.

**Action:** State the partition, class-invariance/adequacy premises and coverage. For the statistical claim identify the 95% one-sided Bernoulli model, independent opportunities and stopping rule.

**Wiki evidence:** L1373–1386, L1638–1638, L1661–1663.

### WIKI-WFD-F07 — Exact-sum WF4 makes the gluing diagnostic redundant

The displayed acceptance formula locally requires each a_i=f(x), so disagreement is impossible after all local passes. WF46 can measure a distinct boundary failure only for weaker local predicates or richer states than those same exact scalar answers. This is a scope limit of the declared instantiation, not evidence that its sum checker is wrong.

**Action:** Describe WF4 exact-sum as isolated repetition with agreement, and specify partial local carriers, restriction maps and a genuinely distinct global evaluator before an LGGR claim.

**Wiki evidence:** L281–287, L1513–1527.

### WIKI-WFD-F08 — WF18 and WF25 need explicit mathematical carrier conditions

No negative cycle is the finite difference-inequality feasibility criterion; an all-weight-1 directed triangle has no negative cycle and satisfies the inequalities with zero potentials but cannot realize every edge as exact potential difference 1. WF25 must retain nontrivial active plaquettes and boundary transports; local flatness does not make every path transport identity or imply global trivialization.

**Action:** State inequality signs for WF18 and retain zero-sum-cycle conditions for exact equalities. For WF25 declare certified block summaries, active plaquette checks, orientation and quotient-loop/gauge assumptions.

**Wiki evidence:** L713–717, L912–927.

**Prior relationship:** papers_audit PFP021 assessment and additional_paper_010_data historical assistance analysis; no C017 model rerun.

### WIKI-WFD-F09 — Design dependencies are not executable or proved compositions

The 75 edges are acyclic and exactly match all Builds-on lists and the registry. Their declared reuse relation supplies no typed port map, task equivalence, execution schedule or soundness theorem. Learn and run A first cannot literally be an execution prerequisite for 44 nodes expressly having no family runner. Hash seals similarly require a trusted anchor and cannot establish semantic task preservation.

**Action:** Call these design/learning dependencies; separately register executable interfaces and task-preserving adapters. Unroll bounded loops and charge positive shared fuel when composing them; do not use an edge as proof authority.

**Wiki evidence:** L3–9, L145–180, L396–408, L1144–1184.

**Prior relationship:** workflows_audit documented design dependencies; papers_audit PFP014/015/016 conditional foundations

### WIKI-WFD-F10 — Design acceptance promises exceed existing checker qualification

The page correctly distinguishes proposals from runners, but exact and dual-independent labels can still read as established guarantees. Earlier source reviews show C049 false terminal/adjunction certificates accepted by both judges, C058 wide false equivalence accepted by both, and C055 valid zero-optimum dual rejected by both. WF22 evaluator rules also differ from the preregistered statistical design. These limit use of all-judge-pass as a generic certificate.

**Action:** Attach per-domain checker qualification/version limits and distinguish normative host contracts from measured implementation behavior. Preserve the exact controls and negative results from existing reviews.

**Wiki evidence:** L494–501, L823–840, L892–898, L1571–1584.

**Prior relationship:** additional_challenges_041_050 C049-1/C049-2; additional_challenges_051_059 C058-F01/AC55-F01; shared_runtime certified_ladder; all cross-references, not new reproductions.

## Per-family assessment

| Family | Reusable mechanism and mathematical scope | Implementation / evidence / transfer limit |
| --- | --- | --- |
| WF1 Typed answer (L188–214) | A frozen typed answer is checked against a declared function. The current example is exact integer sum, not a universal semantic checker. | Implemented family status agrees with the earlier workflow audit. Schema validity and a typed refusal must remain separate from solved mathematical acceptance. No runner rerun here. |
| WF2 Full slots (L215–240) | Required typed slots and explicit absence prevent silent field omission. They do not make an unjustified value true or ensure semantic coverage of an arbitrary task. | Reuse the WF1 domain judge; a new domain needs its own slot interpretation and acceptance predicate. |
| WF3 Mine, then solve (L241–267) | Mining, screening and hash-freezing guidance before an independent solve is a useful experimental boundary. Exact-sum success cannot by itself establish that guidance was useful or answer-free. | The two-call normal path is a recipe count. Freeze and screen each actual guidance payload and compare against a matched baseline before a benefit claim. |
| WF4 Five agents + LGGR (L268–294) | Five isolated proposals can be checked independently, but the displayed local checks already require each answer to equal the same unique f(x). Their agreement is then logically redundant. | A genuine local-green/global-red experiment needs local predicates over partial information and a distinct global compatibility predicate. The exact-sum instantiation cannot estimate nonzero gluing failure. |
| WF5 Checked rewrite (L295–321) | decode(rewrite(s))=query(s) is a meaningful task-preservation contract for the declared whole-input exact-sum grammar. | It does not certify arbitrary prose translation; unsupported language must be refused. Current availability is an implemented restricted runner, not a general rewrite theorem. |
| WF6 Dialect sweep (L322–353) | A fixed query, checked decoders, fixed oracle and item-paired acceptance comparisons are reusable. Net creation/removal counts summarize observations but do not identify a causal mechanism. | Proposal; old capsules and manually invoked trials do not execute this family campaign. Require paired raw observations, missingness, budget and assistance records. |
| WF7 Typed refusal (L354–383) | The displayed rank equality is the criterion for a unique full solution of Ax=b over a declared field with n unknowns. It is stronger than existence of a solution or answerability of a particular query. | Name the requested answer semantics: a consistent rank-deficient system can have valid solutions or a unique queried coordinate. Keep justified impossibility, ambiguity and budget refusal distinct. |
| WF8 Staged sealed packets (L384–413) | Hash chaining detects changes relative to a trusted retained root/head and fixed encoding; typed stage interfaces make boundaries inspectable. | An unkeyed chain can be recomputed after editing. Hashes do not prove provider origin, completeness, meaning preservation or independently trustworthy prior stages. A later repair needs a new downstream chain. |
| WF9 Bounded check-and-repair (L414–444) | A finite attempt cap bounds calls, while residual-based repair needs an allowed edit set and a preserved task. XOR solvability is a cycle-parity condition on the declared graph. | A local residual need not certify minimal repair or progress; specify whether L counts total attempts or repairs after the initial call. Never turn an old expected answer into feedback. |
| WF10 Local-to-global obstruction certificate (L445–476) | H1=ker(delta1)/im(delta0) requires a chain complex with delta1 delta0=0 and a cocycle. A nonzero class obstructs the specified gluing/exactness problem, not arbitrary prose consistency. | Rational Hodge claims need a finite complex and declared positive inner product; integer versus field coefficients matter. Local patches and their restrictions must be explicit. |
| WF11 Dual-certificate synthesis (L477–508) | Primal feasibility, dual feasibility and equal objectives certify LP optimality under the stated sign convention. Farkas, flow/cut, assignment and Bareiss each require their own admitted carrier and witness conditions. | Two named judges are not a soundness proof. Existing C051–C055 reviews record parsing, solver and convention failures; those findings are cross-references, not newly repeated tests. |
| WF12 Mechanism-control arms (L509–538) | Holding the carrier and grader fixed while varying mechanism guidance is a useful ablation design. Rank-difference fixtures only test their declared finite equations. | Explicitly a proposal with an unregistered cited checker; no general mechanism effect follows from planned arms or a paired-rate formula. |
| WF13 Exact-domain capsule battery (L539–570) | Commuting Pauli checks, anomaly equations, group commutators and Regge angles are different domain predicates, not a common solver mechanism. | State phases, admissible stabilizer generators, spacetime/matter assumptions and interior/boundary geometry as appropriate. Planned capsules do not establish physical truth or model performance. |
| WF14 Immune failure classification (L571–601) | Known-good self panels and two-signal admission can separate a pattern trigger from a checked defect. Empirical self tolerance is relative to the nonempty frozen panel. | Zero observed false positives is not a population guarantee. Define both signals, detector version, class coverage and held-out opportunities before admission or transfer. |
| WF15 Adversary tribunal (L602–632) | Independent frozen arguments and a separate finite checker are a useful audit protocol. Kripke truth and grounded argumentation are semantics of a supplied finite model, not truth of unrestricted claims. | Role names and rhetoric do not supply authority. Historical test/mutation counts are not new execution in this review. |
| WF16 Substrate crosswalk (L633–662) | Preserving a presented set of generators and relations can define a homomorphism or functor only with the relevant typing/composition laws. It need not reflect truth, be faithful, or preserve distinctions. | Record all choices and source/target interpretations. A collapse map may preserve relations while losing the original query; require a task-specific reflection/solution map where needed. |
| WF17 Witnessed-difference programme (L663–693) | Finite witnesses, bisimulation and qualified convex duality are useful distinct verification tools. Bisimulation needs a declared labelled transition system; Fenchel–Rockafellar needs actual convexity/properness and qualification assumptions. | A finite witness does not prove a universal equivalence. Cech obstruction language needs a specified coefficient object, cover and cocycle construction; a general gluing problem need not be captured by an abelian H1. |
| WF18 Dossier replay campaign (L694–724) | The 25+5 campaign design and odd-spin-cycle contradiction are precise finite proposals. The no-negative-cycle criterion characterizes feasible difference inequalities, not arbitrary equality-valued potentials. | Declare edge inequality signs and graph finiteness. Reproducing grades authenticates a deterministic replay relationship, not provider origin or checker adequacy. |
| WF19 Failure-derived rule transfer (L725–754) | Disjoint held-out comparisons and self-tolerance checks are necessary design boundaries for rule learning; reference solver outputs correctly remain controls. | A positive observed gain alone is not a reliable population improvement. Reserve confirmation data and account for adaptive rule selection, sample sizes, uncertainty and failed rules. |
| WF20 Derivation loop with lift grants (L755–786) | An explicit lift grant distinguishes admitted extra structure from consequences already established. Finite witness controls and metric/cochain checks remain separate obligations. | The page reports historical five-loop work and expressly leaves proofs unverified. Existing workflow-source review finds answer-bearing legacy controls and dependency gaps; these are not an unassisted general derivation engine. |
| WF21 Structural prompt rewriting (L787–816) | DPO rewriting requires a well-typed span, admissible injective match and gluing conditions. Preserving protected bytes is an independently checkable syntactic invariant. | The protected set must contain every task-bearing dependency. Added contradictory guidance or a lossy decoder can change the effective task despite unchanged protected bytes; keep the exact judge. |
| WF22 Certified cost ladder (L817–847) | Spend per accepted item and paired discordance are useful metrics under a fixed adequate checker and nonzero denominator. | Declare treatment of zero acceptances and missing calls. Existing evaluator review finds H0/H2 and significance-rule gaps; the design formulas are not automatically implemented by its evaluator or historical prose reports. |
| WF23 Judge-packet custody audit (L848–877) | Byte/version custody is useful. The demand that no answer be derivable or a declared function of participant bytes is unsuitable for an ordinary solvable deterministic task. | Replace non-derivability with a declared disclosure/threat model covering answer fields, metadata, feedback and judge access. Existing audit code is bounded lint/probing, not a proof of this goal. |
| WF24 Pinned-token operational scratchpad (L878–905) | Ordered group multiplication is a valid finite certificate computation after declaring identity, inverse, orientation and path. Pinned tokens reduce parsing ambiguity. | Historical C017 3/5 counts depend on retained assisted arms and incomplete baseline payloads. A correct final certificate need not prove every scratchpad line was checked. |
| WF25 Hierarchical decimation (L906–934) | A reduced lattice computation is exact only if every discarded block has an appropriate checked summary and boundary transport. Flatness, trivialization and commuting global holonomy are distinct. | Retain nontrivial active plaquettes as well as noncontractible loops; flat blocks can have nonidentity open-path transport. The historical assisted arm listed active cells/paths. Quad-tree aggregation is still proposed. |
| WF26 Multi-round antibody dialogue (L935–963) | Accumulating typed failure constraints is a bounded repair policy; union of constraints does not ensure consistency, correctness, progress or eventual acceptance. | The page correctly labels historical answer-leaking runs as plumbing only. No independent learned improvement is supported by their reported scores. |
| WF27 Hinted retraction with a stationary-loop detector (L964–992) | A repeat r_t=r_(t-3) detects lag-three recurrence, not stationarity or three consecutive unchanged residuals. A structural lift also needs a task-preservation witness. | The 28-live-trial count repeats a withdrawn owner claim; only eight supplied one-fixture traces are supported by the existing Paper008 review. Full-repair hints demonstrate assisted copying. |
| WF28 Eight-role audit dialogue (L993–1020) | Strict l1 descent can be checked on a fixed admitted defect representation. Descent alone over rationals does not prove finite termination; changed carriers make scores incomparable. | The six run folders are explicitly reference self-scores. Scripted defect traces and role labels must not become measured multi-agent reliability. |
| WF29 Checker synthesis scored by mutation kill rate (L1021–1048) | Mutation kills probe rejection of particular invalid outputs. Accepting all valid examples probes completeness; soundness is rejection of invalid claims (accept implies valid), not zero false rejections. | Neither finite panel establishes general soundness/completeness. C060 historical model scores remain cited claims, not rerun or independently authenticated here. |
| WF30 Constraint-forcing anti-recitation (L1049–1075) | The zero-one principle is exact for a fixed well-formed comparator network over a total order. It does not alone check mandatory prefixes, forbidden comparators or network shape. | Added constraints change the task and must be registered as distinct variants. Failure on them shows constraint failure, not a direct measurement of internal recall or reasoning. |
| WF31 Multi-agent tournament with held-out cross-validation (L1076–1104) | A finite tournament can compare strategies under a declared rational SO carrier and tolerance. Held-out components of one object need not be independent or unpredictable from public symmetries. | The page correctly marks 0/16 versus16/16 as offline, withdrawn earlier rates and live-capable status. Existing PFP020 review reports narrower tests and unchanged-defect mitigation; no live improvement follows. |
| WF32 Claim-scoped receipt (L1105–1133) | Conjunction of sound task-bound predicates certifies only their explicitly bound claims. A correct witness supplies no authority to adjacent prose, universals or quotations. | This is a useful elementary scope mechanism. Registered predicates need adequate semantics and exact payload/witness binding; a Boolean conjunction cannot prove those assumptions. |
| WF33 Recursive re-entry with shared fuel (L1134–1162) | Backward solution and forward coverage maps can preserve a declared task under composition. At most floor(B/delta) operations requires finite B, delta>0 and every operation charged at least delta. | Prevent fuel reset and stale parent, but also bind maps to actual states and payloads. Zero-cost operations or resetting per-child budgets defeat the stated termination bound. |
| WF34 Future-faithful compression and bounded context (L1163–1191) | A finite labelled transition/cost system can be minimized under equal enablement, cost, successor classes and terminal labels. Equal diagnostics are weaker than equal future behavior. | Retaining root/champion/recent attempts is a heuristic context policy, not the proved quotient unless its abstraction satisfies the conditions. The bounded-context arm is explicitly NOT_RUN. |
| WF35 Proposal-channel comparison (L1192–1219) | Channel-invariant acceptance is a design contract: the same final reply is judged by the same predicate, irrespective of proposal channel. | The table retains the null-hook equality and 0/8 outcome; attention/activation options are not live evidence. No guarantee of similar proposal distributions or usefulness follows from oracle invariance. |
| WF36 Guarded staged slot materialisation (L1220–1248) | A guard must cover the full declared syndrome and type/slot obligations; partial observation has a kernel that can hide a defect. | Two admitted optimal results out of 40 measure 2/40 coverage and conditional 2/2 correctness, not dominance over 9/40 exact unstaged results. The claim that a guard removes false-refusal attraction remains limited to the declared mechanism. |
| WF37 Evidence-bound harness evolution (L1249–1278) | Adaptive search with held-out confirmation, transfer panels and multiple-comparison controls is a useful proposed experiment discipline. | UCB1 assumptions need not hold for changing strategies; finite tests do not prove their conditions. Live $40 work is explicitly NOT_RUN; exact sign/paired bootstrap/Holm labels require a prespecified sampling unit and contrasts. |
| WF38 Diagnostic-trace proposal selection (L1279–1307) | An l1 primal-dual certificate needs both h=c+Bf and the displayed dual constraints. Gamma<=\|\|D\|\|Phi needs the compatible induced norm and complex/operator relation. | Host scoring avoids self-report but cannot certify an arbitrary extractor. Fixed-carrier assumptions and task preservation are essential; strict rational descent alone is not termination. |
| WF39 Authority firewall gate (L1308–1336) | AllGuardsPass is a conjunction contract. The obstruction conclusion follows only if zero-defect and other guards are truthful under the intended encoding. | Useful firewall plumbing cannot establish guard adequacy, external truth or completeness. Some guards such as descent/exhaustion need task-specific relevance rather than universal imposition on every run. |
| WF40 Restart boundary after exhausted repair (L1337–1364) | Exact/unclosed/closed-nonexact is a valid partition in a supplied chain complex. Restart, refusal and lift are policy outcomes, not evidence of solved mathematics. | The page correctly calls changed claim sets new problems. Delta>0 needs a defined measure and preservation witness; it cannot license changing the task solely to reduce a score. |
| WF41 Detector adequacy and two-signal admission (L1365–1393) | Representative-set equality implies full equality only when both target and detector are constant on every declared class and every class is represented. | A finite counterexample refutes the displayed unqualified equivalence. Zero-failure bounds near299 also require confidence level, independent opportunities and a fixed sampling/decision protocol; row duplication is not diversity. |
| WF42 Reasoning-trace validation (L1394–1422) | The page appropriately limits Exact to the extractor image and states its adequacy battery is not certified. An exact LP witness can certify the encoded finite graph. | Trace extraction is the semantic boundary: omitted, merged or misinterpreted claims can survive exact downstream arithmetic. Keep CarrierFailure and unadmitted prose explicit. |
| WF43 Gate-honesty and answer-free leak audit (L1423–1450) | Constant outputs, empty objects, keyword attacks and fabricated evidence are useful negative controls against unintended acceptance. | Specify solved acceptance versus lawful typed refusal. If refusal is a permitted correct terminal output for an impossible or out-of-scope task, no-answer-free-reply-passes is too broad; finite attacks cannot prove a universal absence. |
| WF44 Exact certificate presets (L1451–1477) | The written l1 rule conflates the signed cochain with nonnegative objective weights and mismatches the dual bound with its unweighted objective. | An exact triangle counterexample satisfies every displayed condition at objective 12 though the optimum is 6. Use c for claims, positive alpha for weights, alpha-weighted objective and \|z_e\|<=alpha_e, or the unweighted \|z_e\|<=1 rule. |
| WF45 Finite terminal selector and plenitude test (L1478–1506) | Exact/tolerant checks select survivors in a declared finite candidate family; uniqueness is correctly stated relative to that family. | Indistinguishable duplicates illustrate underdetermination but do not construct physical alternatives. Evidence authenticity, candidate completeness and tolerance policy remain supplied premises. |
| WF46 Boundary sufficiency and gluing diagnostic (L1507–1534) | NGD is the conditional frequency/probability of global failure given all local passes; it is correctly undefined when the conditioning event has no observations. | A boundary must preserve the information required by the global evaluator. On the exact-sum WF4 formula, local success already entails agreement, so this preset needs genuinely weaker local checks to be informative. |
| WF47 Resumable bounded frontier search (L1535–1562) | A contiguous replay chain and presentation key containing basis/representation can preserve the search problem and prevent skipped prefixes. | A bounded exhausted suffix establishes only UNKNOWN or a restricted obstruction. It does not exclude unseen solutions or other representations; source labels are not a universal sign-problem solver. |
| WF48 Commit-reveal with a hostile mutation gate (L1563–1591) | Committing task/judge and solver bytes before reveal can bind versions under collision resistance, sufficient salt and independently recorded timing/access controls. | Two judges killing a finite mutant set do not establish soundness or absence of tuning. The all-C043–C060 64/64 and 48/48 sentence overgeneralizes historical self-scores; existing source audits contain contrary checker results. |
| WF49 Query-preservation stage and mode campaign (L1592–1617) | A decoder equality contract can make each representation change testable for a specified family. Per-family oracles and stopping on safety regression are useful campaign constraints. | Explicitly zero campaign cases executed. Seventeen earlier live records do not constitute this campaign or prove a scale effect; preserve original query and task-specific checker assumptions. |

## Validation and evidence limits

Fresh work used only standard-library static checks and small exact finite controls. The WF44 triangle counterexample, WF27 recurrence, WF41 missing-invariance example, WF18 inequality/equality distinction, WF4 agreement implication and soundness/completeness example are recorded in the checks artifact. Conditional 95% zero-failure bounds recompute to about 31.2% for eight independent trials and 0.997% for 299.

Prior workflow, challenge and paper review entries are hash-pinned in the JSON. Their source reads, probes and historical observations are cross-references, not fresh reproduction. Several findings corroborate errors already reported in the PFP021 manuscript; this report establishes their occurrence in the complete wiki page and adds explicit finite controls.

No native build, project suite, provider call, private benchmark access, remote-link verification or original-source mutation occurred. Only this one wiki source receives new full-body coverage; registry parsing and selected prior-report consultation receive no such credit.
