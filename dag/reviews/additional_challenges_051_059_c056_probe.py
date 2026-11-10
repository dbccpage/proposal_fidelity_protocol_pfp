import sys,itertools,random,json
sys.dont_write_bytecode=True
from additional_challenges_051_059_audit import ROOT,write
sys.path.insert(0,str(ROOT/'workflows/tasks/certified_challenges'))
from c056_dfa_minimization_equivalence.reference_solver import solve
from c056_dfa_minimization_equivalence.judge_packet.exact_checker import check_exact as primary
from c056_dfa_minimization_equivalence.judge_packet.independent_checker import independent_check as secondary
def finite_language(text,alphabet,limit=6):
    if type(text)is not str:raise ValueError('non-string regex')
    if not isinstance(alphabet,list) or not alphabet or any(type(x)is not str or len(x)!=1 or x in '%#()*|' for x in alphabet) or len(set(alphabet))!=len(alphabet):raise ValueError('alphabet')
    # A declared whitespace character is a letter, not discarded formatting.
    t=[x for x in text if x in alphabet or not x.isspace()];pos=0
    def mul(a,b):return {x+y for x in a for y in b if len(x+y)<=limit}
    def alt():
        nonlocal pos
        out=seq()
        while pos<len(t) and t[pos]=='|':pos+=1;out|=seq()
        return out
    def seq():
        nonlocal pos
        out={''};count=0
        while pos<len(t) and t[pos] not in ')|':
            c=t[pos];pos+=1
            if c in alphabet:part={c}
            elif c=='%':part={''}
            elif c=='#':part=set()
            elif c=='(':
                part=alt()
                if pos>=len(t) or t[pos]!=')':raise ValueError('unclosed group')
                pos+=1
            else:raise ValueError('illegal atom')
            while pos<len(t) and t[pos]=='*':
                pos+=1;closed={''}
                while True:
                    nxt=closed|mul(closed,part)
                    if nxt==closed:break
                    closed=nxt
                part=closed
            out=mul(out,part);count+=1
        if not count:raise ValueError('missing operand')
        return out
    if not t:return {''}
    result=alt()
    if pos!=len(t):raise ValueError('trailing tokens')
    return result
def run(d,alphabet,w,start=0):
    for x in w:start=d['delta'][start][alphabet.index(x)]
    return start
def bounded_assessment(c,a,limit=6):
    try:
        if a.get('status')!='SOLVED':return {'status':'not_algebraic_certificate'}
        alpha=c['alphabet'];words=[''.join(w) for n in range(limit+1) for w in itertools.product(alpha,repeat=n)]
        if len(words)>25000:return {'status':'not_enumerated','reason':'word budget'}
        mismatches=[];certificate=True
        if c['task']=='MINIMIZE':
            L=finite_language(c['regex'],alpha,limit)
            mismatches=[w for w in words if (run(a,alpha,w) in a['accept'])!=(w in L)]
            certificate=all(run(a,alpha,w)==i for i,w in enumerate(a['access'])) and len(a['access'])==a['states']
            for p in range(a['states']):
                for q in range(p+1,a['states']):
                    z=a['separators'][f'{p},{q}'];certificate &= (run(a,alpha,z,p) in a['accept'])!=(run(a,alpha,z,q) in a['accept'])
        else:
            L=finite_language(c['r1'],alpha,limit);M=finite_language(c['r2'],alpha,limit)
            if a['kind']=='DIFFERENT':
                w=a['word']
                if len(w)>limit:return {'status':'witness_above_length_bound','length':len(w)}
                certificate=(w in L)!=(w in M)
            else:
                mismatches=sorted(L^M)
                for d,lang in ((a['dfa1'],L),(a['dfa2'],M)):mismatches += [w for w in words if (run(d,alpha,w) in d['accept'])!=(w in lang)]
        return {'status':'bounded_membership_assessed','word_limit':limit,'words':len(words),'language_mismatch_count':len(mismatches),'mismatch_examples':mismatches[:4],'local_certificate_equations':bool(certificate),'limits':'Finite-word source binding is not exact whole-language equivalence; owner checkers separately perform exact language decisions.'}
    except Exception as e:return {'status':'invalid_or_assessment_exception','exception':type(e).__name__,'message':str(e)}
MISSING=object()
def evaluate(c,a=MISSING):
    try:a=solve(c) if a is MISSING else a
    except Exception as e:return {'solver_exception':type(e).__name__}
    vs=[]
    for f in (primary,secondary):
        try:vs.append(f(c,a))
        except Exception as e:vs.append({'exception':type(e).__name__})
    return {'answer':a,'owner_verdict':vs,'independent_bounded_language':bounded_assessment(c,a)}
def main():
    rng=random.Random(5607)
    def make(depth):
        if depth==0:return rng.choice(['a','b','%','#'])
        k=rng.randrange(4)
        if k==0:return '('+make(depth-1)+')*'
        if k==1:return '('+make(depth-1)+'|'+make(depth-1)+')'
        if k==2:return '('+make(depth-1)+')('+make(depth-1)+')'
        return make(0)
    cases=[{'case_id':'independent','task':'MINIMIZE','alphabet':['a','b'],'regex':make(3)} for _ in range(128)];failures=[]
    for c in cases:
        e=evaluate(c);b=e['independent_bounded_language']
        if not all(v[0] for v in e['owner_verdict']) or b.get('language_mismatch_count')!=0 or not b.get('local_certificate_equations'):failures.append({'case':c,'evaluation':e})
    controls={}
    for name,alpha,r in [('dot_letter',['.'],'..'),('whitespace_letter',[' '],' '),('alphabet_above_bound',list('abcde'),'a')]:controls[name]=evaluate({'case_id':name,'task':'MINIMIZE','alphabet':alpha,'regex':r})
    controls['non_object']=evaluate(None)
    result={'independent_regexes':len(cases),'word_length_bound':6,'failures':failures,'controls':controls,'limits':'Independent finite language enumeration and direct access/separator arithmetic; no general whole-language proof or provider work.'};write('_c056_probes.json',result);print(json.dumps(result))
if __name__=='__main__':main()
