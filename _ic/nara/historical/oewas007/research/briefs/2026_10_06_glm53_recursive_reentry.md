# GLM5.3 research assignment: reuse of rejection rules without repository access

Copy the text below into GLM5.3. It is self-contained; no repository access is needed.

---

You are deriving a new, narrowly scoped result for the Witnessed Difference Programme (WDP). Your assignment is **reuse of rejection rules and solution methods across changing representations and tasks**. Another researcher is handling realizable observation and instrument costs; do not pursue that topic. Use ordinary mathematical language. Do not invent standards, named protocols, acronyms, or substitutes for definitions. “Antibody” in earlier WDP drafts meant a reusable rejection predicate, not a biological mechanism or a mathematical standard; use “rejection rule.”

Treat this packet as your supplied mathematical data. Do not claim to inspect repository files, run the repository's controller, compile Lean, execute code, obtain an independent review, or complete the entire WDP. You may use a Python sandbox if available, but retain exact inputs, code, outputs, and counterexamples and label unexecuted code explicitly. Browsing is optional: any imported result needs its hypotheses and an accessed primary source. Elementary finite arguments can be derived directly here.

## What is already established (imports, not your new result)

1. A report r:X→Y preserves a question q:X→A exactly when q is constant on every realized r-fiber; its decoder is unique only on r(X).
2. Source candidates X have valid set G_S; target candidates Y have valid set G_T. A total map α:Y→X safely transfers **every** source rejection D⊆X\G_S precisely when α(G_T)⊆G_S. One fixed D needs only α⁻¹(D)∩G_T=∅. For a partial α with domain H, out-of-domain pass-through needs α(G_T∩H)⊆G_S; out-of-domain rejection additionally needs G_T⊆H.
3. A union of individually safe target rejection rules preserves all valid target candidates. Checking only the survivors of an unaudited earlier filter cannot establish this invariant.
4. Backward accepted-witness maps give original-answer soundness. Constructive forward maps give solution coverage. The two duties differ and compose only with their stated domains and commuting original-answer maps.
5. A finite reachability arena has finite states/actions, universal enablement over a belief, nonempty adversarial successor sets, supplied targets, and strictly positive rational action costs. Its winning set is the attractor W₀=T, Wₙ₊₁=Wₙ∪{b:∃a,Succ(b,a)⊆Wₙ}. The complement is a target-disjoint trap. A submitted rank-decreasing policy gives an upper cost bound. Bellman inequalities against **all** admissible actions and a checked loss trap give a lower bound. Removing a safe-looking operation can increase cost or destroy reachability.
6. Re-entry consumes the same fixed fuel ledger. Learning, checking, transport, installation, proposals, and emissions have their declared costs. A recursive call cannot mint a new budget. A receipt is evaluation evidence, not permission to act.

## Frozen question

For the explicit finite packet chain below, derive necessary and sufficient installation conditions separately for (i) original-answer soundness, (ii) coverage of original solutions, and (iii) preservation of a declared worst-case resolution budget. Construct the maps and certificates, rather than repeating conditional map axioms. Then determine exactly which obligations require revalidation when the task parameter, observer, repair/action menu, checker version, or parent packet changes. Produce one compositional successful re-entry and hostile controls.

## Supplied original problem and two representation changes

Let D={−1,0,1}, X₀=D², and d∈{−1,0,1,2}. The original problem P_d asks for a pair (x,y)∈X₀ with x+y=d. Its accepted answers are the actual pairs, not just a yes/no existence bit.

Define

  f₀₁(x,y)=(u,v)=(x+y,x−y),
  X₁=f₀₁(X₀),
  g₁₀(u,v)=((u+v)/2,(u−v)/2),
  f₁₂(u,v)=(r,t)=(u,v+u),
  X₂=f₁₂(X₁),
  g₂₁(r,t)=(r,t−r).

Use **these exact image carriers**, not the enclosing integer boxes. Declare G₀(d)={ (x,y)∈X₀:x+y=d }, G₁(d)={ (u,v)∈X₁:u=d }, and G₂(d)={ (r,t)∈X₂:r=d }. The original-answer decoder at level 2 is g₁₀∘g₂₁. Enumerate all nine carrier elements at every level, verify the inverse and validity laws, and exhibit the composed maps on every solution for d=1.

A proposed rejection rule learned at d=1 is R₁(u,v)≡(u≠1). An actual target-task guard must distinguish that fixed predicate from the parameterized rule R_d(u,v)≡(u≠d). At level 2, transfer through g₂₁, never through field names alone. The out-of-image candidate (u,v)=(1,0) gives a useful domain control: its formal decoder is (1/2,1/2), outside X₀. Do not silently extend the carrier or certify it.

## Supplied operating profile and costs

For any d, the uninstalled search profile can propose any candidate in the current carrier, check it with that packet's declared valid predicate, and emit a valid original answer. Each proposal costs 1, each full validity check costs 2, and emission costs 1. Invalid candidates cannot be emitted and do not mutate an accepted state. Deterministic complete enumeration is permitted; its order must be stated if you claim its budget. Installation of one returned bundle costs 3 total (1 learning + 1 check + 1 install), transport between adjacent levels costs 1, and a guard evaluation costs 1/2 for every candidate occurrence, including repeated candidates. No free or negative-cost loop is admitted. A direct original-profile solution route remains optional unless your installation explicitly removes it.

The shared ledger starts with B=18 and spent s₀=0. Every charged operation appends (parent identity, task d, operation, rational charge, cumulative spent). Re-entry carries the cumulative spent unchanged and may run only when the proposed charge fits the remaining budget. A proposed new grant is outside this packet. Authorization requirement is the fixed uninterpreted token `AUTH-P_d`; a mathematical certificate does not create that token's legitimacy.

You may build a smaller finite operating arena from this profile, but must list every retained/removed operation, adversarial outcome if any, target, price, and initial state. Clearly distinguish the **remaining operating budget** from the **original total budget including setup/transport**. If you claim budget preservation, compare the same original task, same initial conditions, and the same accounting boundary.

## Required hostile controls

1. Changed task d=2: replay the fixed d=1 guard against its actual valid target candidate. Explain which property fails.
2. Stale parent: a bundle bound to d=1/carrier X₁/checker v1 is offered under a different parent digest. Metadata rejection is a custody check; separately show the relevant mathematical mismatch when one exists.
3. Valid-but-blocked solution: remove all allowed valid emissions/proposals while keeping accepted-witness decoding sound. Give an initial-containing loss trap; do not infer loss from a filter violation alone. Also retain an alternate solving route to show the distinction.
4. Fuel reset: attempt to reset spent to zero on re-entry after two transport charges and installation. Calculate the excess exposure and reject the reset.
5. Cost-only failure: a safe bundle retains coverage but raises setup-inclusive cost beyond a protected bound.
6. Checker change: distinguish byte-version change with a proved semantic-equivalence certificate from changed acceptance semantics. State a minimal dependency invalidation rule; 'recheck everything' and 'reuse PASS' are not substitutes for an argument.

## Deep-research-inspired process (maximum six rounds)

**Frame:** restate the frozen problem, hypotheses, three separate completion predicates, domains, lemma DAG, and missing inputs. Any larger goal is a separate proposed mission.

**Produce:** derive in dependency order. Give exact finite tables and a successful installation with backward/forward maps, decoded-answer commutation, admitted action/target/cost preservation where claimed, and one shared ledger. Freeze a named candidate version containing the statements, hypotheses, proof, and certificates.

**Evaluate:** execute exact finite checks if a sandbox exists. Separate source reports, written mathematical arguments, actual finite execution, and formal checking. A hash records bytes; it does not establish validity. Do not declare host PASS on your own authority.

**Challenge:** attack the frozen version with all six controls and any missing hypothesis. A second role or agreement does not count as independent verification. Preserve failed versions and why they failed.

**Repair:** change only the failed dependency, create a new candidate version, and invalidate every affected review/check. Stop after two rounds with the same unresolved semantic residual; report the obstruction precisely.

**Deliver:** a full written result or an exact counterexample at the assigned scope, with a plain-language account of what changed. Use these fields: `statement_and_hypotheses`, `lemma_DAG`, `constructed_maps_and_tables`, `proof`, `successful_reentry_receipt`, `hostile_controls`, `minimal_revalidation_rule`, `cost_and_fuel_ledger`, `evidence_status`, `remaining_obligations`. General engine/world correspondence and institutional authorization remain outside the finite profile.

Do the derivation now. Do not return only a plan or a list of possible research directions.
