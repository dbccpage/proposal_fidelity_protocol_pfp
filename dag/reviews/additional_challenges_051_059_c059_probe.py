"""Public finite SQL controls and per-artifact dispositions, with read-only queries."""
import sys,json,itertools,sqlite3,collections
sys.dont_write_bytecode=True
from additional_challenges_051_059_audit import ROOT,write
sys.path.insert(0,str(ROOT/'workflows/tasks/certified_challenges'))
from c059_sql_null_total_query_synthesis.reference_solver import solve
from c059_sql_null_total_query_synthesis.judge_packet.exact_checker import verify_candidate
from c059_sql_null_total_query_synthesis.judge_packet.independent_checker import independent_check
MISSING=object()
def answer(case,sql,**extra):return {'case_id':case['case_id'],'status':'SOLVED','sql':sql,'preflight_sql':'SELECT 1 WHERE 0','null_ledger':[],**extra}
def evaluate(case,candidate=MISSING):
    if candidate is MISSING:
        try:candidate=solve(case)
        except Exception as e:return {'reference_exception':type(e).__name__,'message':str(e)}
    verdict=[]
    for fn in (verify_candidate,independent_check):
        try:verdict.append(fn(case,candidate))
        except Exception as e:verdict.append({'exception':type(e).__name__,'message':str(e)})
    return {'answer':candidate,'owner_verdict':verdict,'limits':'Results compare only supplied finite database instances. No independent universal query-equivalence proof or dialect-neutral validation is claimed; both judges share schema/bag contracts and SQLite candidate execution.'}
def case(spec,rows=None,schema=None):return {'case_id':'audit_sql','schema':schema or {'t':{'id':'INTEGER'}},'spec':spec,'protected':[],'test_databases':[{'t':rows if rows is not None else [{'id':1}]}]}
def truth(pred,x):
    if 'eq3' in pred:return None if x is None else x==1
    if 'distinct' in pred:return x!=1
    if 'not_distinct' in pred:return x==1
    if 'is_null' in pred:return x is None
    if 'is_not_null' in pred:return x is not None
    if 'not' in pred:
        p=truth(pred['not'],x);return None if p is None else not p
    parts=[truth(p,x) for p in pred.get('and',pred.get('or',[]))]
    if 'and' in pred:return False if False in parts else None if None in parts else True
    return True if True in parts else None if None in parts else False
def main():
    base=case({'op':'select','from':'t'})
    overfit=answer(base,'SELECT 1 AS id')
    changed={**base,'test_databases':[{'t':[{'id':2}]}]}
    distinct=case({'op':'select','from':'t','where':{'distinct':['id',{'val':1}] }},[{'id':None},{'id':1},{'id':2}])
    omission=answer(distinct,'SELECT id FROM t WHERE id IS NOT 1')
    fabricated=answer(base,'SELECT id FROM t /* COALESCE */',null_ledger=[{'node':'nonexistent.path','construct':'COALESCE fabricated trailing words'}])
    affinity=case({'op':'select','from':'t','where':{'eq3':['id',{'val':'01'}]}})
    text=case({'op':'select','from':'t','where':{'coalesce':['id',{'val':0}]}},[{'id':'0'}],{'t':{'id':'TEXT'}})
    nested=case({'op':'rename','from':{'op':'select','from':'t'},'map':{'id':'newid'}},[{'id':1,'other':7}],{'t':{'id':'INTEGER','other':'INTEGER'}})
    semi=case({'op':'semi_join','left':'t','right':'r'},schema={'t':{'id':'INTEGER'},'r':{'other':'INTEGER'}});semi['test_databases'][0]['r']=[{'other':2}]
    projection=case({'op':'project','from':'t','columns':[]})
    rows={'finite_suite_overfit':{'case':base,'on_supplied':evaluate(base,overfit),'on_new_database':evaluate(changed,overfit)},'ledger_and_syntax':{'omitted_required_construct':evaluate(distinct,omission),'fabricated_comment_entry':evaluate(base,fabricated)},'affinity_disagreement':{'case':affinity,'reference':evaluate(affinity),'sqlite_semantics':'INTEGER 1 compares equal to text literal 01 after column affinity; Python scalar equality does not.'},'coalesce_text_truth_disagreement':{'case':text,'reference':evaluate(text)},'nested_rename_drops_column':{'case':nested,'reference':evaluate(nested),'valid_candidate':evaluate(nested,answer(nested,'SELECT id AS newid,other FROM t'))},'missing_join_predicate':{'case':semi,'reference':evaluate(semi),'valid_candidate':evaluate(semi,answer(semi,'SELECT * FROM t WHERE EXISTS (SELECT 1 FROM r)'))},'empty_projection':{'case':projection,'reference':evaluate(projection)}}
    rows['malformed']={'case_null':evaluate(None,{}),'unhashable_status':evaluate(base,answer(base,'SELECT id FROM t',status=[])),'unhashable_operator':evaluate({**base,'spec':{'op':[]}},answer(base,'SELECT id FROM t'))}
    predicates=[({'eq3':['id',{'val':1}]},'id=1'),({'distinct':['id',{'val':1}]},'id IS DISTINCT FROM 1'),({'not_distinct':['id',{'val':1}]},'id IS NOT DISTINCT FROM 1'),({'is_null':'id'},'id IS NULL'),({'is_not_null':'id'},'id IS NOT NULL')]
    eq=predicates[0][0];null=predicates[3][0]
    predicates += [({'not':eq},'NOT (id=1)'),({'and':[eq,null]},'(id=1) AND (id IS NULL)'),({'or':[eq,null]},'(id=1) OR (id IS NULL)')]
    count=0;failures=[]
    for length in range(3):
        for vals in itertools.product([None,0,1],repeat=length):
            for pred,sqlpred in predicates:
                c=case({'op':'select','from':'t','where':pred},[{'id':v} for v in vals]);a=answer(c,'SELECT id FROM t WHERE '+sqlpred);v=evaluate(c,a)['owner_verdict'];count+=1
                con=sqlite3.connect(':memory:');con.execute('CREATE TABLE t(id INTEGER)');con.executemany('INSERT INTO t VALUES (?)',[(x,) for x in vals]);got=[x[0] for x in con.execute(a['sql'])];con.close();expected=[x for x in vals if truth(pred,x) is True]
                if collections.Counter(got)!=collections.Counter(expected) or not all(isinstance(x,(tuple,list)) and x[0] for x in v):failures.append({'values':vals,'predicate':pred,'expected':expected,'got':got,'verdict':v})
    rows['independent_kleene_bag_controls']={'cases':count,'mismatches':failures,'limits':'Exhaustive bags of length 0..2 over NULL,0,1 and eight separately written predicates; no general relational-algebra completeness or mixed-affinity claim.'}
    write('_c059_probes.json',rows);print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
