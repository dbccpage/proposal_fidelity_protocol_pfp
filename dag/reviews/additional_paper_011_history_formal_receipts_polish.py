import sys,json
sys.dont_write_bytecode=True
import additional_paper_011_history_formal_receipts_audit as a
rows=a.read('_automated.json');md=a.file('.md').read_text(encoding='utf8')
for r in rows:
    for c in r['checks']:
        if c['rule']=='receipt_or_manifest_fields' and len(c.get('keys',[]))>100:
            c['key_count']=len(c['keys']);c['sample_keys']=c.pop('keys')[:2]
            c['limit']='Complete typed runtime-map check appears separately; only two keys are displayed here to avoid duplicating the full historical map.'
a.write('_automated.json',rows);a.report()
for old,new in [('frozen446','frozen 446'),('partition:71','partition: 71'),('covering6331','covering 6,331'),('and375','and 375'),('bytes:39','bytes: 39'),('slice:0','slice: 0'),('All102','All 102'),('All446','All 446'),('compared:201','compared: 201'),(',82',', 82'),(',163',', 163'),('for442','for 442'),('the225','the 225'),('final446','final 446'),('all1014','all 1,014'),(';52','; 52'),('/13',' / 13'),('in12','in 12'),('/141',' / 141'),('and1530','and 1,530'),('F5/1','F 5/1'),('L3/1','L 3/1')]:md=md.replace(old,new)
a.file('.md').write_text(md,encoding='utf8')
c=a.read('_completion_receipt.json');c['report_sha256']=a.sha(a.file('.json'));c['markdown_sha256']=a.sha(a.file('.md'));a.write('_completion_receipt.json',c)
print(json.dumps({'report_sha256':c['report_sha256'],'markdown_sha256':c['markdown_sha256'],'report_bytes':a.file('.json').stat().st_size,'source_reads':71,'bounded_data':375,'findings':3,'current_stream_mismatches_resolved_to_zip':83}))
