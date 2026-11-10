"""Read-only whole XML inventory and all text labels; no SVG rendering or scripts."""
import collections,hashlib,json,pathlib,xml.etree.ElementTree as E
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_pfp_infrastructure_remaining';f=json.loads((H/(P+'_preparation.json')).read_text())['files'];out=[]
for i in(373,375):
 q=f[i];b=(R/q['path']).read_bytes();assert hashlib.sha256(b).hexdigest()==q['sha256'];root=E.fromstring(b);els=list(root.iter());texts=[''.join(e.itertext())for e in els if e.tag.split('}')[-1]=='text'];links=[(e.tag,k,v)for e in els for k,v in e.attrib.items()if'href'in k or k.lower().startswith('on')]
 row={'path':q['path'],'sha256':q['sha256'],'lines':q['lines'],'tag_counts':dict(collections.Counter(e.tag.split('}')[-1]for e in els)),'root_attributes':root.attrib,'all_text_labels':texts,'links_and_event_attributes':links,'scripts':sum(e.tag.split('}')[-1]=='script'for e in els),'review_level':'bounded_complete_XML_inventory_and_all_text_labels_not_full_source_body'};out.append(row);print(json.dumps(row,ensure_ascii=False,indent=2))
(H/(P+'_visuals.json')).write_text(json.dumps(out,indent=2)+'\n')
