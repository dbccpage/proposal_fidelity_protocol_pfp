"""Read exact named first-party archive owners; never extract or execute bundles."""
import difflib,hashlib,json,sys,tarfile
from pathlib import Path
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]; P='additional_paper_004'
OUT=HERE/(P+'_inspection'); PKG=ROOT/'papers/pfp/004_pfp_native_verification_and_evidence_custody'
TAR=PKG/'audited_source/pfp-iv-native-source-52cb5457.tar.gz'
PREFIX='pfp-iv-native-source-52cb5457/'
def sha(b): return hashlib.sha256(b).hexdigest()
def main(args):
    ledgerpath=HERE/(P+'_archive_read_ledger.json')
    ledger=json.loads(ledgerpath.read_text()) if ledgerpath.exists() else []
    with tarfile.open(TAR) as t:
        for arg in args:
            name,sep,rng=arg.partition('::'); m=t.getmember(PREFIX+name); b=t.extractfile(m).read(); lines=b.decode().splitlines()
            a,z=map(int,rng.split('-')) if sep else (1,len(lines))
            assert 1<=a<=z<=len(lines)
            print('MEMBER',name,'LINES',len(lines),'SHA256',sha(b))
            for i in range(a,z+1): print(f'{i}: {lines[i-1]}')
            ledger.append({'archive_path':str(TAR.relative_to(ROOT)).replace('\\','/'),'archive_sha256':sha(TAR.read_bytes()),'member':PREFIX+name,'sha256':sha(b),'line_count':len(lines),'reviewed_lines':[[a,z]]})
    ledgerpath.write_text(json.dumps(ledger,indent=2)+'\n')
if __name__=='__main__': main(sys.argv[1:])
