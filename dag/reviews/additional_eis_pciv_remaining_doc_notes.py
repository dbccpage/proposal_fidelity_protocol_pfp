"""Assessments after complete ordinary prose bodies, diagrams and snippets were read."""
LEVEL_NOTES = {
"00": "Separates genome content identity from execution occurrences and declares generation derivation. The stated four-field identity excludes protected_spans, conflicting with the current source test that demands different span sets yield different IDs. SHA-256 collision resistance is an assumption; the prose claim that every change always yields a distinct digest is stronger than a finite hash can guarantee.",
"01": "Defines inheritance versus citation graphs and acyclicity as separate obligations. Graph separation alone does not establish acyclicity or that a sealed receipt proves physical generation. F-RANK-01 is used for reference invariance here but for pass-fraction sensitivity in Level 05/tests; align identifiers before treating this as a traceable contract.",
"02": "Specifies protected byte spans, wild birth custody and future externally enacted meta policies. The displayed half-open overlap formula misses zero-width insertions, while the later text requires insertion protection; production test has a distinct zero-width control. No-self-admission and elimination of all authorization exploits are conditional architecture obligations, not consequences of byte overlap alone.",
"03": "States anchored acquisition, shortest inheritance-hop distance, exact dyadic weights for hops 1 through 10 and separate global revocation. The backward formula names origin-to-ancestor directed distance despite parent-to-child edge orientation; it needs an explicit reversed traversal. Dyadic law/horizon are declared policy, not biological optimality; inherited references are not new observations or admissions.",
"04": "Declares exact Pareto fronts, separate compliance, assigned-task evidence and exploration quotas. Obligation-ID equality is necessary but not sufficient for verified fitness: current tests reject caller dicts and self-seals even with matching IDs. All-maximize dominance requires a declared benefit orientation for cost/latency. Refusal credit depends on the task branch and cannot imply solved-task credit.",
"05": "Provides an explicit row-stochastic inverse matrix, 17/20 damping and normalized nonnegative rational fixed-point obligation solved by Gaussian elimination. This is a useful finite mathematical contract given graph/evidence inputs. Distinct-digest deduplication and pass fractions need trusted acquisition; exact arithmetic alone does not prove broad sybil resistance or empirical superiority.",
"06": "Specifies admitted placement/covering read scope, seven lexicographic keys and per-contribution floored half-life decay; the local matching owner violates the mandatory-placement premise. The full level uses floor(t/H), while its short concept and notebook use continuous decay. Priority guarantees are conditional on the other lexicographic keys remaining fixed; decay alone does not prove lack of entrenchment.",
"07": "Defines exact fractions 3/5, 1/4, 3/20, floor-plus-largest-remainder allocation, declared tie order, redistribution and shelving distinct from custody. N=10 gives 6/3/1 under these premises. Some current tests expect 12/6/2 at N=20, which differs from this formula's 12/5/3; quota policy needs reconciliation, not a claim of a universal optimal ecology.",
"08": "Defines global rule-version invalidation separately from forward causal least fixed point and OR taint. The prose claims formal proof and mathematically verified isolation but supplies no proof artifact here. Current finite test fixtures do not prove arbitrary ordering/concurrency closure; a diagnostic label is distinct from enforcing retrieval/reproduction quarantine.",
"09": "Describes producer event identity, payload conflicts, CAS checks and captured-response replay with explicit unknown outcomes. Interface snippets are schematic and differ from tested signatures. Hash chains do not by themselves guarantee crash consistency, concurrency or external anchoring; source/test recovery behavior and durability assumptions remain necessary.",
"10": "Explicit v0.2 research roadmap for crossover, migration, frozen settlement and resource allocation, not delivered or benchmarked mechanisms. Its short lesson marks maturity production/claim_status verified despite this roadmap ceiling. Metabolism here means budget allocation, whereas reviewed IntelligenceMetabolism owners index/segment/mine retained records; those capabilities must not be conflated.",
}

def documentation_note(path):
    name = path.rsplit("/", 1)[-1]
    if "/levels/level_" in path:
        return LEVEL_NOTES[name.split("_")[1]]
    if "/concepts/lesson_" in path:
        level = name.split("_")[2]
        special = {
            "04": " The short lesson names raw cost and latency yet gives a universal >= dominance rule without orienting those minimized axes.",
            "05": " The short lesson says power iteration terminates on exact duality-gap certificates, whereas Level 05 explicitly specifies Gaussian elimination and a fixed-point certificate; those are different algorithms/checks.",
            "06": " The short formula omits the floor in the full level's exact stepwise half-life policy.",
            "10": " The production/verified front matter conflicts with its explicit future horizon.",
        }.get(level, "")
        return "Short curriculum guide, including production/verified front matter, concepts and questions, read in full. " + LEVEL_NOTES[level] + special + " Its companion notebook is assessed separately; a lesson label is not verification evidence."
    if "/curriculum/" in path and name == "README.md":
        return "Track/navigation document read in full; lists lessons, workbenches, storyboard and video directories. Directory markers do not establish populated media or delivered instruction. Described mechanism ambitions must retain the narrower source and notebook evidence ceilings."
    if "authenticated_custody_20261012" in path:
        return "Historical bounded checkpoint read in full, including commands, tables and explicit single-worker/no-provider limits. It distinguishes signed fixture interoperability from actual host measurement, trust enrollment, external ledger pins and statistical independence. Pass counts were not rerun and are not new execution receipts."
    if "epic_boundary_repair_20261012" in path:
        return "Historical bounded checkpoint read in full, including failed global checks, platform skip and original dirty-tree caveat. The 21 retained embedded-output hash mismatches are recorded separately; its claimed byte bindings are not silently accepted. Commands were not rerun and source-located papers were not opened."
    if "oeeis_epic_closeout_20261027" in path:
        return "Historical relocated closeout read in full. Explicitly reports one Python failure caused by an absent git object, three skips, ten detected/restored mutations, native compilation fix and nonexecuted full/Windows/CI scopes. Rename-map paths are historical presentation, not fresh command or source-byte verification."
    return None
