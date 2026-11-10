"""Inspect public capsule fields; no seeds, private inputs, model calls or mutations."""
import argparse, collections, hashlib, json
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'pilots/anomalon_woland'
OUT=Path(__file__).with_name('numbered_051_101_capsules.json')
def evidence(p,fields):
    raw=p.read_bytes()
    return {'path':p.relative_to(ROOT).as_posix(),'lines':[1,len(raw.decode('utf-8').splitlines())],
            'sha256':hashlib.sha256(raw).hexdigest(),'review_level':'parsed_public_fields_not_full_text_review','fields_reviewed':fields}
def main():
    parser=argparse.ArgumentParser(); parser.add_argument('lo',type=int);parser.add_argument('hi',type=int)
    args=parser.parse_args(); rows=[]
    for i in range(51,102):
        row={'pilot':i,'capsules':[]}
        for p in sorted((BASE/f'pilot_{i:07d}/tests').glob('test_*/input.yaml')):
            d=yaml.safe_load(p.read_text(encoding='utf-8')); sp=p.with_name('test_spec.yaml'); t=yaml.safe_load(sp.read_text(encoding='utf-8'))
            prompt=d.get('user_prompt',''); schema=d.get('response_schema',{})
            if isinstance(schema,str):
                schema=yaml.safe_load(schema)
            entry={'test':p.parent.name,'input_evidence':evidence(p,['user_prompt','response_schema','lineage']),
              'test_spec_evidence':evidence(sp,['test_id','expected_outcome','actual_outcome','notes','checker_registered']),
              'test_id':t.get('test_id'),'user_prompt':prompt,'response_schema_sha256':hashlib.sha256(json.dumps(schema,sort_keys=True).encode()).hexdigest(),
              'answer_schema':schema.get('properties',{}).get('answer'), 'expected_outcome':t.get('expected_outcome'),
              'actual_outcome':t.get('actual_outcome'),'notes':t.get('notes'),'lineage':d.get('lineage')}
            row['capsules'].append(entry)
        rows.append(row)
        if args.lo<=i<=args.hi:
            print('\nPILOT',i)
            for c in row['capsules']:
                print(c['test'],c['test_id'])
                if i>=55: print(c['user_prompt'].split('Return one JSON object')[0].strip())
                elif i==52:
                    print(c['user_prompt'])
                else:
                    print('EXPECTED',c['expected_outcome'],'NOTES',c['notes'])
    OUT.write_text(json.dumps(rows,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    generated=[c for r in rows if r['pilot']>=55 for c in r['capsules']]
    print('GENERATED SCHEMA HASHES',dict(collections.Counter(c['response_schema_sha256'] for c in generated)))
    print('ANSWER SCHEMAS', {json.dumps(c['answer_schema'],sort_keys=True) for c in generated})
if __name__=='__main__':main()
