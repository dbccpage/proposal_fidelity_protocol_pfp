"""C041 offline controls; uses only an already installed native Lean binary."""
import os, sys, json, itertools, hashlib, collections
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from additional_challenges_041_050_audit import ROOT, file, read, write, record
native=Path(r'C:\Users\a343o\.elan\toolchains\leanprover--lean4---v4.35.0\bin')
assert (native/'lean.exe').exists()
os.environ['PATH']=str(native)+os.pathsep+os.environ['PATH']
tmp=file('_tmp'); tmp.mkdir(exist_ok=True)
os.environ['TMP']=os.environ['TEMP']=str(tmp)
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'workflows/tasks/certified_challenges'))
from c041_lean4_finite_lemma_proofs.judge_packet.checkers.dual_evaluator import evaluate_dual
from c041_lean4_finite_lemma_proofs.reference_solver import lean_compiler as lc

def evaluate(label, case, answer):
    try: result=evaluate_dual(case,answer)
    except Exception as e: result={'exception':type(e).__name__,'message':str(e)}
    return {'label':label,'case':case,'answer':answer,'result':result}

if __name__=='__main__':
    ans={'case_id':'audit','status':'SOLVED','kind':'PROOF','aux':[],'proof':'by decide'}
    case={'case_id':'audit','statement':'2 + 2 = 4','prelude':''}
    controls=[evaluate('valid_independent_arithmetic',case,ans),
       evaluate('false_arithmetic_reject',{**case,'statement':'2 + 2 = 5'},ans),
       evaluate('missing_case_and_answer_ids',{'statement':'2 + 2 = 4','prelude':''},{k:v for k,v in ans.items() if k!='case_id'}),
       evaluate('unwhitelisted_open_command_in_aux',case,{**ans,'aux':['def helper : Nat := 0\nopen Nat']}),
       evaluate('nonstring_prelude',{**case,'prelude':1},ans),
       evaluate('unhashable_status',case,{**ans,'status':[]}),
       evaluate('unbounded_prop_has_no_required_decidable_instance',{**case,'statement':'∀ n : Nat, n = n'},{**ans,'proof':'by intro n; rfl'}),
       evaluate('unknown_is_not_proof',case,{'case_id':'audit','status':'UNKNOWN','code':'SEARCH_LIMIT_REACHED'})]
    math={'quadratic_residue_mod_11':{'witness':5,'square_mod_11':25%11,'expected_kind':'PROOF','generator_label':'REFUTATION'},
          'all_prime13_nonzero_products_nonzero':all(a*b%13!=0 for a in range(1,13) for b in range(1,13)),
          'composite12_counterexample':[3,4,3*4%12]}
    write('_c041_probes.json',{'native_lean':str(native/'lean.exe'),'version':lc.lean_version(),'controls':controls,'independent_math':math,
       'limits':['Installed Lean 4.35.0 differs from TASK 4.34.1 and CHALLENGE 4.34.0; no requested version was installed.','These are bounded native controls, not fresh verification of every retained proof.']})
    print(json.dumps({'controls':[(r['label'],r['result'][0] if isinstance(r['result'],tuple) else r['result']) for r in controls],'version':lc.lean_version()}))
