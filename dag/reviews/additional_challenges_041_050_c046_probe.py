import sys,itertools
sys.dont_write_bytecode=True
from additional_challenges_041_050_audit import ROOT,write
sys.path.insert(0,str(ROOT/'workflows/tasks/certified_challenges'))
from c046_knuth_bendix_completion.reference_solver.solver import solve
from c046_knuth_bendix_completion.judge_packet.checkers.dual_evaluator import evaluate_dual
def main():
    rows=[]
    def run(name,c,a=None):
        try:
            if a is None:a=solve(c)
            result=evaluate_dual(c,a)
        except Exception as e:result={'exception':type(e).__name__,'message':str(e)}
        rows.append({'name':name,'case':c,'answer':a,'result':result})
    c={'case_id':'probe','equations':[['f(f(x))','f(x)']]}
    run('idempotence control',c)
    run('fabricated budget exhaustion',{**c,'max_steps':1000000},{'case_id':'probe','status':'REFUSED','reason':'MAX_STEPS_EXCEEDED','witness':{}})
    a=solve(c);a.pop('joinability_certificates');a['joinability_certificates_count']=999;run('invented join count no paths',c,a)
    a={'case_id':'probe','status':'SOLVED','converged':True,'rules_count':1,'rules':[{'lhs':'f(x)','rhs':'x'}],'joinability_certificates_count':0}
    run('stronger identity unsound under constant0 finite model',c,a)
    r={'case_id':'probe','task':'REDUCE','rules':[['a','b'],['a','c']],'term':'a'}
    run('two distinct reachable irreducible normal forms',r)
    a=solve(r);a['term']='unrelated';run('unbound echoed target term',r,a)
    run('cyclic system confluence normalization exception',{'case_id':'probe','task':'CHECK_CONFLUENCE','rules':[['a','b'],['a','c'],['b','a'],['c','a']]})
    # Every directed acyclic ground rewriting relation on four constants, independently closed.
    edges=[(i,j) for i in range(4) for j in range(i)];bad=[]
    for mask in range(1<<len(edges)):
        chosen=[e for k,e in enumerate(edges) if mask>>k&1];reach=[{i} for i in range(4)]
        for i,j in chosen:reach[i].add(j)
        for k in range(4):
            for i in range(4):
                if k in reach[i]:reach[i]|=reach[k]
        confluent=all(reach[a]&reach[b] for s in range(4) for a in reach[s] for b in reach[s])
        case={'case_id':'finite','task':'CHECK_CONFLUENCE','rules':[[chr(97+i),chr(97+j)] for i,j in chosen]}
        answer=solve(case); verdict=evaluate_dual(case,answer)
        if answer['is_confluent']!=confluent or not verdict[0]:bad.append({'mask':mask,'truth':confluent,'answer':answer,'verdict':verdict})
    write('_c046_probes.json',{'controls':rows,'ground_acyclic_relations':{'systems':64,'mismatches':bad},'independent_unsoundness_model':{'universe':[0,1],'f':[0,0],'equation_f_f_x_equals_f_x':True,'f_x_equals_x_at1':False},'limits':'Finite ground confluence enumeration does not prove arbitrary first-order completion correct.'})
    print([(r['name'],r['result']) for r in rows]);print('64 finite graphs mismatches',len(bad))
if __name__=='__main__':main()
