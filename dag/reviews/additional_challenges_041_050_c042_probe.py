"""Independent bounded SAT truth tables and adversarial certificates; offline only."""
import sys, itertools, json
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
from additional_challenges_041_050_audit import ROOT, write
sys.path.insert(0,str(ROOT/'workflows/tasks/certified_challenges'))
from c042_sat_with_drat_certificates.judge_packet.checkers.dual_evaluator import evaluate_dual
from c042_sat_with_drat_certificates.reference_solver.solver import solve, format_dimacs_cnf
from c042_sat_with_drat_certificates.reference_solver.sat_solver import solve_cnf
from c042_sat_with_drat_certificates.reference_solver.drat_engine import DRATVerifier, verify_drat_certificate, compute_sha256

def truth(cs,n=2):
    return any(all(any(bits[abs(x)-1]==(x>0) for x in c) for c in cs) for bits in itertools.product([False,True],repeat=n))
def control(label,case,answer=None):
    out={'label':label,'case':case}
    try:
        if answer is None: answer=solve(case)
        out.update(answer=answer,verdict=evaluate_dual(case,answer))
    except Exception as e: out.update(exception=type(e).__name__,message=str(e))
    return out
if __name__=='__main__':
    clauses=[list(c) for choice in itertools.product([-1,0,1],repeat=2) for c in [[(i+1)*v for i,v in enumerate(choice) if v]]]
    failures=[]; count=0;rat_checks=0
    for mask in range(1<<len(clauses)):
        cs=[c for i,c in enumerate(clauses) if mask>>i&1]; expected=truth(cs)
        sat,model,proof=solve_cnf(2,cs); count+=1
        proof_ok=None if sat else verify_drat_certificate(format_dimacs_cnf(2,cs),proof)[0]
        if sat!=expected or (not sat and not proof_ok): failures.append({'clauses':cs,'expected':expected,'owner':sat,'proof_ok':proof_ok})
        verifier=DRATVerifier(2,cs)
        for c in clauses:
            if c and verifier.check_rat(c,c[0]):
                rat_checks+=1
                if truth(cs+[c])!=expected: failures.append({'RAT_preservation_failure':[cs,c]})
    case={'case_id':'audit','family':'coloring','n':2,'k':2,'edges':[[0,1]]}
    cnf='p cnf 1 999\n1 0\n-1 0\n'
    unsat={'case_id':'wrong','status':'SOLVED','kind':'UNSAT','proof_format':'DRAT','proof_text':'0\n1 0','cnf_sha256':compute_sha256(cnf)}
    controls=[control('wrong_id_accepted',case,{'case_id':'wrong','status':'SOLVED','kind':'SAT','solution':{'colour':[0,1]}}),
      control('negative_vertex_python_indexing',{**case,'edges':[[-1,0]]},{'status':'SOLVED','kind':'SAT','solution':{'colour':[0,1]}}),
      control('header_mismatch_and_nonterminal_empty_clause_accepted',{**case,'cnf_text':cnf},unsat),
      control('genuine_header_mismatch_refusal_rejected',{'case_id':'audit','family':'coloring','cnf_text':cnf}),
      control('nonpositive_dimensions_refusal_rejected',{'case_id':'audit','family':'php','pigeons':0,'holes':0}),
      control('raw_satisfiable_cnf_decoder_missing',{**case,'cnf_text':'p cnf 4 1\n1 0\n'}),
      control('blocked_tile_unconstrained_decoder',{'case_id':'audit','family':'tiling','rows':1,'cols':2,'blocked':[[0,0]],'tiles':[[[0,0]],[[0,1]]]}),
      control('false_refusal_witness_accepted',{'case_id':'audit','family':'fiction'},{'status':'OUT_OF_SCOPE','witness':{'reason':'VERTEX_OUT_OF_RANGE','field':'imaginary'}}),
      control('nonbinary_charges_accepted',{'case_id':'audit','family':'tseitin','vertices':2,'edges':[[0,1]],'charges':[2,2]}, {'status':'SOLVED','kind':'SAT','solution':{'edge_values':[0]}})]
    write('_c042_probes.json',{'independent_truth_table_formulas':count,'accepted_rat_additions_checked_for_equisatisfiability':rat_checks,'failures':failures,'controls':controls,
       'limits':['All512 clause-set formulas over2 variables; not a proof for arbitrary formulas.','CNF/problem equivalence is a trusted generator premise when cnf_text is supplied; contradictory supplied representations expose that admission.','No CaDiCaL, drat-trim, LRAT, network, or provider calls.']})
    print(json.dumps({'truth_tables':count,'rat_checks':rat_checks,'failures':len(failures),'controls':[(r['label'],r.get('verdict',[r.get('exception')])[0]) for r in controls]}))
