"""Losslessly factor repeated historical log lines for complete reading."""
from pathlib import Path
import copy
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'dag/reviews/paper_005_support_inspection'
PACKAGE = ROOT/'papers/pfp/005_pfp_practitioners_field_manual'
paths = ['code/paper_033_execution_receipt.json','code/cross_domain_symbol_game_receipt.json',
    'docs/release_validation_2026_10_01.json','docs/release_validation_2026_10_02.json',
    'docs/publication_review_2026_10_02.json']

def unique(items):
    result = {}
    for k,v in items:
        assert k not in result,k
        result[k] = v
    return result

receipts = []
for index,rel in enumerate(paths):
    raw = (PACKAGE/rel).read_bytes()
    obj = json.loads(raw.decode('utf-8-sig'),object_pairs_hook=unique)
    pool,strings = [],[]
    def encode(value):
        if isinstance(value,dict): return {k:encode(v) for k,v in value.items()}
        if isinstance(value,list): return [encode(v) for v in value]
        if isinstance(value,str) and '\n' in value:
            ids = []
            for line in value.splitlines(keepends=True):
                if line not in pool: pool.append(line)
                ids.append(pool.index(line))
            strings.append(ids)
            return {'__exact_log_string__':len(strings)-1}
        return value
    def decode(value):
        if isinstance(value,dict):
            if set(value) == {'__exact_log_string__'}:
                return ''.join(pool[i] for i in strings[value['__exact_log_string__']])
            return {k:decode(v) for k,v in value.items()}
        if isinstance(value,list): return [decode(v) for v in value]
        return value
    encoded = encode(copy.deepcopy(obj))
    assert decode(encoded) == obj
    text = ['SOURCE '+rel,'COMPLETE_METADATA_AND_VALUES',json.dumps(encoded,indent=2,ensure_ascii=False),
        'COMPLETE_STRING_LINE_SEQUENCES',json.dumps(strings), 'COMPLETE_UNIQUE_LOG_LINES']
    text += [str(i)+' '+json.dumps(line,ensure_ascii=False) for i,line in enumerate(pool)]
    target = OUT/f'receipt_{index:02d}_lossless.txt'
    target.write_text('\n'.join(text)+'\n',encoding='utf-8')
    receipts.append({'path':(PACKAGE/rel).relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),
        'view':target.relative_to(ROOT).as_posix(),'unique_log_lines':len(pool),'strings_reconstructed':len(strings),
        'view_lines':len(target.read_text(encoding='utf-8').splitlines()),'view_bytes':target.stat().st_size,
        'full_read':False})
(OUT/'receipt_view_preparation.json').write_text(json.dumps(receipts,indent=2)+'\n',encoding='utf-8')
print(json.dumps(receipts,indent=2))
