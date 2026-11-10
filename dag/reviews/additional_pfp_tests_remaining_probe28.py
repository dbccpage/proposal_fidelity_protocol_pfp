"""AST-extract read-vetted lexical tests and feed comment-only synthetic source."""
import sys,ast,math,json
sys.dont_write_bytecode=True
import additional_pfp_tests_remaining_audit as a
p='pfp/tests/test_symbol_game_master_mutation_battery.py'
source='\n'.join(a.source(p))
names=['test_f_symgam_003_epics_crate_has_no_pyo3','test_f_symgam_005_seven_distinct_acts_and_host_identity','test_f_symgam_006_orientation_reversal_refusal','test_f_symgam_007_debate_logarithmic_bound','test_f_symgam_011_genesis_empty_quiz_refusal','test_f_symgam_012_exact_guards_and_blank_reviewer','test_f_symgam_013_probing_eigenvalues_refusal','test_f_symgam_014_coda_layer_bridging_refused','test_f_symgam_015_library_citation_never_proof_and_census']
markers=['Act::TerminalRealityGate','Act::Verification','Act::CochainRepair','Act::GaugeBreak','Act::Descent','Act::Projection','Act::Intake','Act::Intake','fn same_carrier_identity','transport_called: false','OrientationReversed','DisagreementLocalizationEngine','the_round_count_stays_within_the_declared_bound','EmptyQuiz','ExaminerReceiptV1','core.symbol.genesis_examiner.v1','GuardScope::Exact','UnreviewedGeneralization','EigenvaluesNotExact','characteristic_polynomial','SeamCrossing','CitationIsNotProof','DECLARED_TOTAL_PLACEMENTS: u32 = 5_000;']
comments='\n'.join('// '+s for s in markers)
class FakePath:
    def __truediv__(self,_):return self
    def exists(self):return True
    def read_text(self,**_):return comments
    def with_suffix(self,_):return self
    def glob(self,_):return []
g={'REPO_ROOT':FakePath(),'math':math}
selected=[n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name in names]
assert len(selected)==len(names)
exec(compile(ast.Module(body=selected,type_ignores=[]),'<read-vetted lexical tests>','exec'),g)
out=[]
for name in names:
    g[name]();out.append({'test':name,'status':'passed_on_comment_only_source'})
result={'runtime':sys.version.split()[0],'source':{'path':p,'sha256':a.row(p)['sha256']},'method':'Only9read-vetted lexical FunctionDefs, fake path objects, stdlibmath. No real foreignowner reads, nativeinit, providers or testcollection.','controls':out,'synthetic_body':'Comments only; Act names intentionally reversed withduplicateIntake; no declarations/implementations.','limits':'Demonstrates weakness of static marker assertions, not that actual Rust owners are incorrect.'}
a.write('_probe28.json',result);print(json.dumps({'count':len(out),'all_passed':True}))
