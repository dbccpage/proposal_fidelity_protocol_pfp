"""Bounded current metadata checks for dated wiki assertions; no skill execution."""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[2];REV=ROOT/'dag/reviews'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
catalog_path=ROOT/'operads/skill_operad/json/capability_catalog.v1.json';c=load(catalog_path)
slice_path=ROOT/'operads/skill_operad/json/agent_capability_slices.json';a=load(slice_path)
rows=[]
for p in sorted((ROOT/'operads/skills').glob('*/SKILL.md')):
    text=p.read_text(encoding='utf-8-sig');m=re.match(r'^---\s*\n(.*?)\n---(?:\s*\n|$)',text,re.S)
    assert m,p
    v=yaml.safe_load(m.group(1));name=v['name'];errors=[]
    if not isinstance(name,str) or not 1<=len(name)<=64 or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',name):errors.append('Agent Skills name format')
    if name!=p.parent.name:errors.append('name differs from directory')
    description=v.get('description')
    if not isinstance(description,str) or not 1<=len(description)<=1024:errors.append('description length/type')
    rows.append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'name':name,'format_issues':errors})
assert len(rows)==237
spec_dir=ROOT/'eis/antibodies/specs';specs=[]
for p in sorted(spec_dir.glob('*.yaml')):
    q=p.parent.parent/p.name
    specs.append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'root_exists':q.is_file(),
                  'root_equal_bytes':p.read_bytes()==q.read_bytes() if q.is_file() else None})
out={'scope':'Whole current frontmatter/catalog counts; not complete skill bodies, runtime binding verification or external host compatibility tests.',
     'catalog':{'path':catalog_path.relative_to(ROOT).as_posix(),'sha256':sha(catalog_path),
                'skills':len(c['skills']),'agents':len(c['agents']),
                'executor_states':dict(Counter(x['executor']['state'] for x in c['skills'])),
                'residual_effects':dict(Counter(x['residual_effect'] for x in c['skills']))},
     'agent_slices':{'path':slice_path.relative_to(ROOT).as_posix(),'sha256':sha(slice_path),'agents':len(a['agents'])},
     'skill_frontmatter_records':rows,'skill_format_issue_count':sum(bool(x['format_issues']) for x in rows),
     'antibody_spec_copies':specs,
     'external_primary_sources':[
         {'url':'https://agentskills.io/specification','accessed':'2026-11-10','assessment':'Spec forbids consecutive hyphens in names, requires directory agreement and bounds name/description lengths. The current garden is not uniformly compliant. This check covers those fields only, not every optional format condition.'},
         {'url':'https://modelcontextprotocol.io/specification/2025-06-18/server/tools','accessed':'2026-11-10','assessment':'Output schemas are optional. When supplied, conformant structured results are required from servers and client validation is recommended. The wiki should not describe schema validation as universally observed enforcement by every host.'},
         {'url':'https://openai.com/index/agentic-ai-foundation/','accessed':'2026-11-10','published':'2025-12-09','assessment':'Announcement supports donation of AGENTS.md and MCP to AAIF under the Linux Foundation. It does not establish the wiki claims about universal host enforcement or compatibility.'}],
     'limits':['Metadata BOUND is not a freshly replayed executor correctness certificate.','Reading archived SKILL.md frontmatter for audit does not invoke any skill or follow its body instructions.','No remote skill/platform execution, provider calls or private answer access.']}
(REV/'additional_wiki_inventory_checks.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'catalog':out['catalog'],'slice_agents':len(a['agents']),'name_issues':out['skill_format_issue_count'],'invalid_names':[x['name'] for x in rows if x['format_issues']], 'spec_files':len(specs),'same_bytes':sum(x['root_equal_bytes'] is True for x in specs)}))
