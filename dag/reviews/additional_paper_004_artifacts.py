"""Read-only archive custody, complete ZIP deltas and PDF rendering aids."""
import difflib
import hashlib
import json
import subprocess
import tarfile
import zipfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PREFIX = "additional_paper_004"
NAME = "004_pfp_native_verification_and_evidence_custody"
PACKAGE = ROOT / "papers/pfp" / NAME
OUT = HERE / (PREFIX + "_inspection")
OUT.mkdir(exist_ok=True)

def sha(raw): return hashlib.sha256(raw).hexdigest()
def lf(raw): return raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
def write(path, value): path.write_text(json.dumps(value, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
def present(name): return name.replace("_lev_landau_", "_lev_examiner_").replace("_pfp_landau_companion.pdf", "_pfp_examiner_companion.pdf")
def entries(raw):
    result = {}
    for line in lf(raw).splitlines():
        if not line or line.startswith("#"): continue
        digest, relative = line.split("  ", 1)
        assert len(digest)==64 and relative not in result
        p=PurePosixPath(relative)
        assert not p.is_absolute() and ".." not in p.parts and "\\" not in relative
        result[relative]=digest
    return result

def archives():
    result = {"current_manifests":[], "zip_members":[], "zip_manifests":[], "tar_members":[], "limits":"All member bytes hashed; no semantic review follows automatically. Exact/LF equality and deltas are transfer aids only until base and full delta readings are recorded."}
    for name in ("MANIFEST.sha256", "SHA256SUMS"):
        rows=[]
        for rel, digest in entries((PACKAGE/name).read_bytes()).items():
            p=PACKAGE/rel;assert p.resolve().is_relative_to(PACKAGE.resolve())
            row={"path":rel,"expected_sha256":digest,"exists":p.is_file()}
            if p.is_file():
                raw=p.read_bytes();row.update(actual_sha256=sha(raw),raw_match=sha(raw)==digest)
                try:row["lf_match"]=sha(lf(raw).encode())==digest
                except UnicodeDecodeError:row["lf_match"]=None
            rows.append(row)
        result["current_manifests"].append({"path":name,"entries":rows})
    with zipfile.ZipFile(PACKAGE/(NAME+"_2026-10-02.zip")) as z:
        assert z.testzip() is None
        assert len(z.namelist())==len(set(n.casefold() for n in z.namelist()))
        for index, info in enumerate(z.infolist()):
            p=PurePosixPath(info.filename);assert not p.is_absolute() and ".." not in p.parts
            assert p.parts[0]==NAME
            rel=p.relative_to(NAME).as_posix();raw=z.read(info);now=PACKAGE/present(rel)
            row={"member":info.filename,"sha256":sha(raw),"bytes":len(raw),"current_path":now.relative_to(ROOT).as_posix(),"mode":info.external_attr>>16}
            if now.is_file():
                current=now.read_bytes();row.update(current_sha256=sha(current),current_raw_equal=raw==current)
                try:
                    before,after=lf(raw),lf(current);row["current_lf_equal"]=before==after
                    if before!=after:
                        delta="".join(difflib.unified_diff(before.splitlines(keepends=True),after.splitlines(keepends=True),fromfile="archive/"+rel,tofile="current/"+present(rel)))
                        target=OUT/f"zip_delta_{index:02d}.txt";target.write_text(delta,encoding="utf-8")
                        row.update(complete_diff_path=target.relative_to(ROOT).as_posix(),complete_diff_lines=len(delta.splitlines()))
                except UnicodeDecodeError:row["current_lf_equal"]=None
            else:row["current_missing"]=True
            result["zip_members"].append(row)
        for name in ("MANIFEST.sha256","SHA256SUMS"):
            manifest=z.read(NAME+"/"+name);parsed=entries(manifest)
            result["zip_manifests"].append({"path":name,"sha256":sha(manifest),"entries":len(parsed),"missing":[rel for rel in parsed if NAME+"/"+rel not in z.namelist()],"mismatches":[rel for rel,d in parsed.items() if NAME+"/"+rel in z.namelist() and sha(z.read(NAME+"/"+rel))!=d]})
    inventory=json.loads((ROOT/"dag/file_inventory.json").read_text(encoding="utf-8"))
    statuses={r['path']:r for r in json.loads((HERE/'coverage.json').read_text(encoding='utf-8'))['files']}
    index=defaultdict(list)
    for row in inventory['files']:index[row['sha256']].append(row['path'])
    tarpath=PACKAGE/'audited_source/pfp-iv-native-source-52cb5457.tar.gz'
    manifest=entries((PACKAGE/'audited_source/SOURCE_MEMBERS.sha256').read_bytes())
    with tarfile.open(tarpath,'r:gz') as t:
        members=t.getmembers();seen=set()
        for m in members:
            p=PurePosixPath(m.name);assert not p.is_absolute() and '..' not in p.parts
            assert m.isfile() and m.name not in seen;seen.add(m.name)
            rel=PurePosixPath(*p.parts[1:]).as_posix();raw=t.extractfile(m).read();digest=sha(raw)
            matches=index.get(digest,[])
            reviewed=[x for x in matches if statuses[x]['substantive_status']=='full_text_source_review_recorded']
            result['tar_members'].append({'member':m.name,'sha256':digest,'bytes':m.size,'manifest_match':manifest.get(rel)==digest,'mode':m.mode,'mtime':m.mtime,'original_inventory_equal_paths':matches,'prior_full_read_equal_paths':reviewed})
    result['tar_summary']={'members':len(result['tar_members']),'manifest_entries':len(manifest),'all_manifest_digests_match':all(r['manifest_match'] for r in result['tar_members']),'current_inventory_exact_match_count':sum(bool(r['original_inventory_equal_paths']) for r in result['tar_members']),'prior_full_read_exact_match_count':sum(bool(r['prior_full_read_equal_paths']) for r in result['tar_members']),'nested_archives':[r['member'] for r in result['tar_members'] if r['member'].endswith('.zip')]}
    write(HERE/(PREFIX+'_custody.json'),result)
    print(json.dumps({'zip_members':len(result['zip_members']),'zip_deltas':sum('complete_diff_path' in r for r in result['zip_members']),'zip_manifests':result['zip_manifests'],'current_manifest_counts':[{ 'path':r['path'],'rows':len(r['entries']),'raw_failures':sum(not e.get('raw_match') for e in r['entries']),'unresolved_after_lf':sum(not(e.get('raw_match') or e.get('lf_match')) for e in r['entries'])} for r in result['current_manifests']],'tar_summary':{k:v for k,v in result['tar_summary'].items() if k!='nested_archives'}}))

def pdfs():
    from pypdf import PdfReader
    from PIL import Image, ImageDraw
    poppler=Path(r'C:\Users\a343o\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdftoppm.exe')
    rows=[];byhash={}
    for index,path in enumerate(sorted(PACKAGE.rglob('*.pdf'))):
        digest=sha(path.read_bytes());reader=PdfReader(path)
        texts=[p.extract_text(extraction_mode='layout') or '' for p in reader.pages]
        extraction=OUT/f'pdf_{index:02d}.txt';extraction.write_text('\n'.join(f'\nPAGE {i+1}\n{s}' for i,s in enumerate(texts)),encoding='utf-8')
        row={'path':path.relative_to(ROOT).as_posix(),'sha256':digest,'pages':len(texts),'extraction':extraction.relative_to(ROOT).as_posix()}
        if digest in byhash:row['raw_equal_render_base']=byhash[digest]
        else:
            folder=OUT/f'pdf_render_{index:02d}';folder.mkdir(exist_ok=True)
            subprocess.run([str(poppler),'-scale-to','1500','-png',str(path),str(folder/'page')],check=True,capture_output=True,timeout=60)
            pages=sorted(folder.glob('page-*.png'),key=lambda p:int(p.stem.split('-')[-1]));assert len(pages)==len(texts)
            row['page_images']=[p.relative_to(ROOT).as_posix() for p in pages]
            sheets=[]
            for offset in range(0,len(pages),4):
                sheet=Image.new('RGB',(2100,3060),'white');draw=ImageDraw.Draw(sheet)
                for k,page in enumerate(pages[offset:offset+4]):
                    with Image.open(page) as im:
                        thumb=im.convert('RGB');thumb.thumbnail((1030,1500))
                    x,y=(k%2)*1050,(k//2)*1530;draw.text((x+10,y+5),f'PDF {index:02d} PAGE {offset+k+1}',fill='black');sheet.paste(thumb,(x+(1050-thumb.width)//2,y+25))
                target=folder/f'sheet-{offset//4+1:02d}.png';sheet.save(target);sheets.append(target.relative_to(ROOT).as_posix())
            row['sheets']=sheets;byhash[digest]=row['path']
        rows.append(row);print(json.dumps({'pdf':index,'pages':len(texts),'same_bytes_as':row.get('raw_equal_render_base')}),flush=True)
    write(OUT/'pdf_inventory.json',rows)

if __name__=='__main__':
    import sys
    if sys.argv[1]=='archives':archives()
    elif sys.argv[1]=='pdfs':pdfs()
