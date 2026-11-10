"""Persist completed governance source/log readings without inflating artifact coverage."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REV=ROOT/'dag/reviews'
scope=json.loads((REV/'additional_governance_remaining_scope.json').read_text())
frozen={row['path']:row for row in scope['files']}
target=REV/'additional_governance_remaining.json'
report=json.loads(target.read_text()) if target.exists() else {'file_reviews':[]}
rows={row['path']:row for row in report['file_reviews']}
notes={
 'governance/tools/metrics.py':'Read all metric bands, Python AST nesting, C# masking/brace nesting, report and CLI code. Grade bands are policy thresholds, not mathematical or empirical quality estimates. Missing metrics cap nothing but remain explicitly null. The C# claim that brace depth never understates control nesting is false for unbraced conditionals; the exact owner-function probe reports0 for four nested if statements. No complexipy/lizard or C# compiler run.',
 'governance/tools/mutation.py':'Read all six outcome definitions, AST/lexical mutation operators, cache/journal handling, subprocess classification, equivalents and CLI. The exact ratio counts unrun and inconclusive cases against success, excluding declared equivalent/invalid cases. Equivalent status relies on a hash-bound written justification, not an equivalence prover. A per-campaign cache permits same-size same-second bytecode reuse, independently reproduced. Journal restoration occurs after the target loop/finally, not literally after each mutant; no production campaign was run.',
 'governance/tools/tests/__init__.py':'Empty package marker inspected in its test-package context; no executable or mathematical content.',
 'governance/tools/tests/conftest.py':'Read the complete temporary-repository fixture. It copies the real policy, starts an empty baseline and supplies one governed module plus a deliberately empty test. Git writes target the pytest temporary directory. This defines test infrastructure, not evidence the production repository passes. Fixture not invoked.',
 'governance/tools/tests/test_baseline.py':'Read all baseline and language-tag tests. Tests distinguish explicit reasoned grandfathering from automatic shrinking and preserve exact source hashes. Admitting a Rust or Lean label is schema acceptance rather than compilation or proof. These tests do not independently validate historical baseline semantics; not rerun.',
 'governance/tools/tests/test_checker_pins.py':'Read all checker edge controls, tolerance tests, CLI requirements and strict-record tests. A1e-9 tolerance is deliberately used for mutation-ratio reports; source digests, level bases and declared evidence are separate. The fresh-input fixture is a supplied record rather than authenticated execution. Tests were not rerun or promoted to general checker soundness.',
 'governance/tools/tests/test_mutation_pins.py':'Read defaults, lexical masking, integer mutation and cross-target budget tests. They check reported outcomes and final restoration, but not equal-size same-second bytecode collisions or per-mutant restoration. Their integer/index expectations pin the declared operator population; passing them would not establish semantic coverage.',
 'governance/tools/tests/test_tool_pins.py':'Read all evidence and metric edge tests. Boundary grades, elif treatment, braced C# members, JSON serialization and timeout output are useful finite controls. The C# examples all use braces and therefore miss the unbraced nesting counterexample. No original test suite executed.',
 'governance/tools/tests/test_tools.py':'Read complete evidence, metrics, Python/C# mutation, journal recovery, timeouts and command-runner tests. Exact counts and conservative ratio are useful bounded controls. Baseline success plus a collection-error substring does not authenticate causal attribution to a mutant. Existing C# and cache examples omit the newly reproduced edge cases. No real governed target was mutated.',
}
log_notes={
 'csharp-tests.log':'All29 named historical pass lines and the0-failure summary read. Includes cross-language receipts, transport/refusal and cancellation tests. It is a retained transcript, not fresh execution or a proof of all C# behavior.',
 'dotnet-build.log':'Complete historical build-success transcript read: zero warnings/errors and8.07seconds. No source binding or new build follows from this text alone.',
 'import-linter.log':'Complete historical54-file/192-dependency report read: two contracts kept. Static dependency restrictions are narrower than semantic purity or runtime I/O confinement.',
 'metrics.log':'Complete one-line48-file historical metric summary read. Lowest ceilingB is a policy result, not a correctness proof.',
 'mypy-strict.log':'Complete43-source success line read. Historical type checking is separate from functional correctness and present-source identity.',
 'pfp-cli-clippy.log':'Complete historical Rust clippy completion log read. It names a Linux checkout and build profile; no current Windows build was performed.',
 'pfp-cli-fmt.log':'Empty retained formatter output inspected. Empty output alone cannot prove success; the accompanying run record is a separate binding.',
 'pfp-cli-metrics.log':'Complete seven-file historical metric summary read. Lowest ceilingB is conditional on the measured metric implementation and source version.',
 'pfp-cli-mutants.log':'Complete230-mutant transcript read:192caught,4missed,33unviable,1timeout; counts sum230. Conservative eligible ratio would be192/197 when unviable is excluded and timeout retained. Missed wrap/color/read-lines mutants and timeout remain visible; no fresh campaign or inference that the current Python cache defect affected this Rust run.',
 'pfp-cli-test.log':'Complete historical31CLI plus21library test names, zero-test targets, paths and summaries read. All52named tests are reported passing. This is transcript evidence, not a fresh run or native binary/source proof.',
 'pfp-cli-wasm.log':'Complete historical development-profile completion line read; it does not by itself identify a fully executed Wasm test.',
 'pytest-all.log':'Complete386-pass historical output and dependency deprecation warning read. Names/source bindings require the run record; no current suite execution.',
 'pytest-optimized.log':'Complete386-pass historical optimized-run output read. Pytest explicitly warns ordinary assertions outside rewritten test modules may be disabled. Passing this suite is narrower than proving all optimized-mode runtime checks survive.',
 'ruff-check.log':'Complete historical all-checks-passed line read. Lint success is not semantic validation.',
 'ruff-format.log':'Complete48-files-already-formatted line read. Formatting carries no mathematical correctness claim.',
 'workflow-migration-final-tests.log':'Complete201-pass historical migration log read with128.69second duration. The final label does not supply independent model or provider evidence.',
 'workflow-migration-tests.log':'Complete201-pass earlier migration log read with102.82second duration. A second retained run is not automatically an independent experiment.',
}
notes.update({'governance/evidence/'+name:note for name,note in log_notes.items()})
notes.update({
 'governance/__init__.contract.score.json':'Complete namespace-package contract, score and history read. It declares L4D with C/C/C/D/A+ gates, a D ceiling and explicit mutation/live-evidence deficits. Package extension and retained 201-test/27-wheel claims are bounded engineering evidence, not mathematical certification or fresh executions. The is_complete flag means a completed assessment, not passing all possible correctness obligations.',
 'governance/evidence/metrics.json':'All48 historical rows read. C# cognitive complexity is explicitly null. Metric ceilings are policy bands; the table does not prove correctness. Mutation cyclomatic complexity12 and test_boundaries nesting4 are B. No lizard/complexipy replay or claim that historical source identity is supplied by this table alone.',
 'governance/evidence/pfp-cli-metrics.json':'All seven Rust metric rows read. check.rs nesting4 and main.rs cyclomatic14 yield B ceilings; cognitive values are null. Non-Python nesting uses a C# brace heuristic in the owner implementation, so this is a retained heuristic report, not a Rust AST measurement or proof of software correctness.',
 'governance/evidence/workflow-live-round-metrics.json':'All seven historical workflow rows read. Runtime, task and runner ceilings range from A+ through D, with wf0003/4/5 runner cyclomatic maxima27/30/31. The evidence honestly includes low grades. These complexity measurements do not establish model efficacy, answer correctness or current-source binding.',
 'governance/evidence/workflow-review-fixes-metrics.json':'All seven historical review-fix rows read. Accounting cyclomatic19 is C; wf0003 workflow cognitive29 and wf0004 runner cyclomatic30 impose D. Names and measurements describe a historical snapshot, not an independently authenticated improvement experiment.',
 'governance/evidence/equivalents.json':'Complete37-entry exclusion declaration read. Justifications concern slot layout, unreachable defaults, bounded reads, zip length guards, metric table lengths, synchronization contexts, BOM output, window visibility and child processes. They can support equivalence only under the stated observation/caller assumptions; they are not unrestricted program equivalence proofs. Hashes and mutation identities are checked separately. In particular changing slots changes object layout, and changing console visibility remains observable outside the restricted protocol view.',
})
for path,note in notes.items():
    data=(ROOT/path).read_bytes()
    assert hashlib.sha256(data).hexdigest()==frozen[path]['sha256']
    lines=len(data.decode('utf-8').splitlines())
    rows[path]={'path':path,'sha256':frozen[path]['sha256'],'full_source_read':True,
                'reviewed_lines':[[1,lines]] if lines else [],'assessment':note}
def evidence(path):
    return {'path':path,'sha256':frozen[path]['sha256']}
report.update(source_commit=scope['source_commit'],status='in_progress',
              scope_manifest='dag/reviews/additional_governance_remaining_scope.json',
              file_reviews=sorted(rows.values(),key=lambda row:row['path']),
              pending_paths=sorted(set(frozen)-set(rows)))
report['claims']=[{
 'id':'GOV-C01','statement':'The governance mutation ratio is killed/(killed+survived+inconclusive+unrun), with null for an empty denominator. This is a conservative accounting convention over a declared mutation population, not a probability of program correctness or a proof that all equivalent mutants were correctly excluded.',
 'evidence':[evidence('governance/tools/mutation.py'),evidence('governance/tools/tests/test_tools.py')],
 'validation_status':'Full source and tests read; no general campaign rerun.'}]
report['findings']=[
 {'id':'GOV-F01','statement':'C# brace-depth counting can understate control nesting despite its docstring guarantee. Four nested unbraced if statements yield nesting0 and A+ for that metric, although depth4 falls in bandB. The braced positive control returns2.',
  'evidence':[evidence('governance/tools/metrics.py'),evidence('governance/tools/tests/test_tool_pins.py')],
  'validation':'dag/reviews/additional_governance_remaining_probes.json',
  'limits':'Actual selected owner functions on synthetic valid-form C# text; no C# compilation or proof that the overall multi-metric grade of a production file changes.',
  'recommended_action':'Use a C# syntax/control-flow analysis or report this as a brace-depth heuristic without the never-understates claim.'},
 {'id':'GOV-F02','statement':'One bytecode cache per mutation campaign does not prevent stale execution between equal-size mutants with the same timestamp second. The controlled actual-method probe labels both mutants killed; using a fresh cache for the second yields exit0, so it should survive. Reused bytecode can inflate the measured kill count.',
  'evidence':[evidence('governance/tools/mutation.py'),evidence('governance/tools/tests/test_mutation_pins.py')],
  'validation':'dag/reviews/additional_governance_remaining_probes.json',
  'limits':'Controlled timestamp collision with bytecode enabled and selected owner methods. It demonstrates a reachable failure mode, not its prevalence or occurrence in retained historical campaigns.',
  'recommended_action':'Invalidate or isolate bytecode for every tested mutant, or load verified current source bytes without timestamp-cache reuse; add the equal-size/same-second control.'},
]
report['limits']=['Source/log and six small JSON bodies read; remaining artifact dispositions are recorded by the separate population-check finalizer.',
                  'No original source writes, provider calls, native builds, private benchmark access or historical test campaign replay.']
target.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'full':len(rows),'pending':len(report['pending_paths']),'claims':len(report['claims']),'findings':len(report['findings'])}))
