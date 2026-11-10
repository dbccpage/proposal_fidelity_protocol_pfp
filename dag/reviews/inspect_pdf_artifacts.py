"""Read-only PDF extraction and duplicate census, never mathematical validation."""
from pathlib import Path
import hashlib,json
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'dag/reviews/pdf_text';OUT.mkdir(exist_ok=True)
inventory=json.loads((ROOT/'dag/file_inventory.json').read_text(encoding='utf-8'))
rows=[r for r in inventory['files'] if r['path'].lower().endswith('.pdf')]
cache={};records=[]
for i,row in enumerate(rows):
    digest=row['sha256']
    if digest not in cache:
        record={'sha256':digest,'representative_path':row['path'],
                'review_level':'pdf_structure_and_text_extraction_only',
                'mathematical_content_review_complete':False,'visual_review_complete':False}
        try:
            reader=PdfReader(ROOT/row['path'])
            pages=[p.extract_text() or '' for p in reader.pages]
            text='\n\n'.join(f'--- PAGE {n+1} ---\n{s}' for n,s in enumerate(pages))
            name=digest+'.txt';(OUT/name).write_text(text,encoding='utf-8')
            record.update(status='extracted',page_count=len(pages),text_characters=len(text),
                          low_text_pages=[n+1 for n,s in enumerate(pages) if len(s.strip())<40],
                          extracted_text='dag/reviews/pdf_text/'+name,
                          extracted_text_sha256=hashlib.sha256(text.encode()).hexdigest())
        except Exception as e:record.update(status='extraction_failed',error=type(e).__name__+': '+str(e)[:300])
        cache[digest]=record
    records.append({'path':row['path'],'sha256':digest,'content_record':digest})
    if (i+1)%20==0:print(json.dumps({'processed_pdfs':i+1,'unique_contents':len(cache)}),flush=True)
result={'status':'format_inspection_complete_semantic_and_visual_review_incomplete',
        'scope':'Every eligible tracked PDF at pinned main; identical bytes share a content record.',
        'source_commit':inventory['local_head'],'files':records,'contents':list(cache.values()),
        'limits':['Extracted text can omit or distort mathematical notation, figures and layout.',
                  'No equivalence to source manuscripts is asserted from filenames or duplicate titles.']}
(ROOT/'dag/reviews/pdf_artifacts.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'pdfs':len(rows),'unique_contents':len(cache),'pages':sum(r.get('page_count',0) for r in cache.values()),
                  'failures':sum(r['status']!='extracted' for r in cache.values())}),flush=True)
