"""Emit bounded pinned source segments for substantive manual review; no execution."""
from pathlib import Path
from hashlib import sha256
import argparse
import json

ROOT=Path(__file__).resolve().parents[2]
PREFIX=ROOT/'dag/reviews/additional_challenges_011_020'

def inventory():
    rows=json.loads((ROOT/'dag/file_inventory.json').read_text())['files']
    return [r for r in rows if r['path'].startswith('workflows/tasks/certified_challenges/') and any('/c%03d_'%n in r['path'] for n in range(11,21))]

def batches(number):
    rows=[r for r in inventory() if '/c%03d_'%number in r['path'] and Path(r['path']).suffix in ('.py','.md')]
    groups=[];group=[];size=0
    for row in rows:
        path=ROOT/row['path'];lines=path.read_text(encoding='utf-8').splitlines()
        start=1;piece=[];piece_size=0
        for i,line in enumerate(lines,1):
            if piece and piece_size+len(line)+20>18000:
                segment=dict(path=row['path'],sha256=sha256(path.read_bytes()).hexdigest(),start=start,end=i-1,text=piece)
                if size+piece_size>20000 and group:groups.append(group);group=[];size=0
                group.append(segment);size+=piece_size;piece=[];piece_size=0;start=i
            piece.append(line);piece_size+=len(line)+20
        segment=dict(path=row['path'],sha256=sha256(path.read_bytes()).hexdigest(),start=start,end=len(lines),text=piece)
        if size+piece_size>20000 and group:groups.append(group);group=[];size=0
        group.append(segment);size+=piece_size
    if group:groups.append(group)
    return groups

def main():
    parser=argparse.ArgumentParser();parser.add_argument('family',type=int);parser.add_argument('batch',type=int,nargs='?');args=parser.parse_args()
    groups=batches(args.family)
    if args.batch is None:
        print(json.dumps(dict(family=args.family,batches=len(groups),segments=[[(s['path'],s['start'],s['end']) for s in g] for g in groups]),indent=2));return
    group=groups[args.batch]
    for segment in group:
        print(f"FILE {segment['path']} SHA256 {segment['sha256']} LINES {segment['start']}-{segment['end']}")
        print('\n'.join(f'{i}: {line}' for i,line in enumerate(segment['text'],segment['start'])))
    # These are emission records, not assertions of semantic completeness.
    log=Path(str(PREFIX)+'_emitted_segments.jsonl')
    with log.open('a',encoding='utf-8') as out:
        for s in group:out.write(json.dumps({k:v for k,v in s.items() if k!='text'}|{'family':args.family,'batch':args.batch,'status':'emitted_for_manual_review'})+'\n')

if __name__=='__main__':main()
