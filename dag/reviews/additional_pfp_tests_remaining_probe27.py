"""Independent finite arithmetic and serialization countercontrols; no owner imports."""
import sys,json,itertools,math
sys.dont_write_bytecode=True
import additional_pfp_tests_remaining_audit as a
def order(p):
    seen=set();lengths=[]
    for x in range(len(p)):
        if x in seen:continue
        y=x;n=0
        while y not in seen:
            seen.add(y);n+=1;y=p[y]
        lengths.append(n)
    return math.lcm(*lengths)
orders=[order(p) for p in itertools.permutations(range(5))]
glyph='\u237a';wire=json.dumps({'detail':glyph},ensure_ascii=True)
result={'runtime':sys.version.split()[0], 'method':'Independent stdlib arithmetic/serialization only; no repository source imports except audit helper.', 'glyph_control':{'raw_glyph_retained_in_object':True,'test_absence_assertion_passes':glyph not in wire,'decoded_object_still_contains_raw_glyph':json.loads(wire)['detail']==glyph},'permutation_control':{'permutations':len(orders),'max_order':max(orders),'size':5,'two_and_three_cycle_order':order((1,0,3,4,2))},'c5_large_successor_exponent_mod5':(10**18+2)%5,'modular_convention':{'minus17_mod5':-17%5,'ten_pow30_mod7':pow(10,30,7)},'limits':'Confirms selected test arithmetic and counterexample to escaped-serialization evidence. Does not execute glyph/row owners or establish pin/history authenticity.'}
assert result['glyph_control']['test_absence_assertion_passes'] and max(orders)==6
a.write('_probe27.json',result);print(json.dumps(result))
