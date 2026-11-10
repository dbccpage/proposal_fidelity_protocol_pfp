// Read-only inventory of paper source. Hashing is never treated as substantive review.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const cp = require('child_process');
const root = process.cwd();
const out = 'dag/reviews/papers_audit.json';
const old = fs.existsSync(out) ? JSON.parse(fs.readFileSync(out, 'utf8')) : {};
const oldFiles = new Map((old.files || []).map(x => [x.path, x]));
const oldPapers = new Map((old.papers || []).map(x => [x.path, x]));
const files = [];
const tracked = new Set(cp.execFileSync('git',['ls-files','-z','--','papers'],{encoding:'utf8'}).split('\0').filter(Boolean));
function walk(dir) {
  for (const ent of fs.readdirSync(dir, {withFileTypes:true})) {
    if (ent.isDirectory() && ent.name.startsWith('.')) continue;
    const p = `${dir}/${ent.name}`;
    if (ent.isDirectory()) walk(p);
    else {
      if (!tracked.has(p)) continue;
      const b = fs.readFileSync(p);
      const ext = path.extname(p).toLowerCase();
      const binary = ['.pdf','.zip','.gz','.png','.exe','.bin'].includes(ext);
      let kind = binary ? 'generated-or-packaged-binary' : ['.lean'].includes(ext) ? 'formal-proof-source' : ['.py','.rs','.sh','.bat','.lua'].includes(ext) ? 'executable-source' : ['.json','.jsonl','.oeos-envelope','.xml'].includes(ext) ? 'structured-data-or-receipt' : ext === '.tex' ? 'typesetting-source-or-rendering' : ext === '.md' ? 'prose-source-or-documentation' : ext === '.ipynb' ? 'notebook' : 'metadata-or-other-text';
      const prev = oldFiles.get(p) || {};
      const sha256=crypto.createHash('sha256').update(b).digest('hex');
      const changed=prev.sha256 && prev.sha256!==sha256;
      files.push({...prev, path:p, bytes:b.length, sha256, kind, review_status:changed?'changed-since-prior-inventory-not-reread':(prev.review_status || (binary ? 'binary-inventoried-not-rendered' : 'inventoried-not-substantively-read')), reviewed_ranges:changed?[]:(prev.reviewed_ranges || []), ...(changed?{prior_snapshot:{sha256:prev.sha256,review_status:prev.review_status,reviewed_ranges:prev.reviewed_ranges}}:{})});
    }
  }
}
walk('papers');
const byHash = new Map();
for (const f of files) {
  const prev = byHash.get(f.sha256);
  if (prev) f.exact_duplicate_of = prev;
  else byHash.set(f.sha256, f.path);
}
const papers=[];
for (const series of ['pfp','non_pfp']) for (const e of fs.readdirSync(`papers/${series}`,{withFileTypes:true})) {
  if(!e.isDirectory() || !/^\d{3}_/.test(e.name)) continue;
  const dir=`papers/${series}/${e.name}`;
  const candidates=files.filter(f=>path.posix.dirname(f.path)===dir && f.path.endsWith('.md') && !/(?:README|REVIEW_SCOPE|_math_spine|_claim_ledger|_change_log)\.md$/.test(f.path));
  const primary=candidates.find(f=>/\/paper\.md$/.test(f.path)) || candidates.find(f=>!/^\d{3}_/.test(path.posix.basename(f.path))) || candidates[0];
  const prev=oldPapers.get(dir)||{};
  papers.push({...prev,path:dir,series,primary_manuscript:primary?.path||null,review_status:prev.review_status||'not-yet-read',verdict:prev.verdict||'not-established',verdict_scope:prev.verdict_scope||'No substantive verdict until review; not-established refers to audit evidence only.',findings:prev.findings||[],actions:prev.actions||['Complete primary manuscript, proof, source-reference, and reproduction audit.']});
}
const output={...old,schema_version:1,scope:{root:'papers',exclude:'Git-untracked files and directories whose names start with a dot; no private benchmark or answer-key storage accessed.',inventory_count:files.length,inventory_bytes:files.reduce((a,f)=>a+f.bytes,0),numbered_paper_count:papers.length,unique_byte_contents:byHash.size,local_head:cp.execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim(),remote_main_verified_by_parent:'8050c66900899771766f33e8f5fdd200b7dd9120',prior_local_head:'644d950a44c6387d7ebc669c098bf4de91168771',note:'Metadata and cryptographic hashes do not imply substantive reading. Checkout is now at the verified remote commit; unchanged prior reads retain their status, changed bytes are invalidated.'},completion_status:'in-progress; full-source audit unfinished',papers,files};
fs.writeFileSync(out,JSON.stringify(output,null,2)+'\n');
console.log(JSON.stringify({...output.scope,reviewed_files:files.filter(f=>f.review_status==='full-text-read').length}));
