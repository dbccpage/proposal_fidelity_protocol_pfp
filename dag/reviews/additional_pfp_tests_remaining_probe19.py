"""Small lexical census countercontrols; no Rust body imports or builds."""
import sys
sys.dont_write_bytecode=True
import ast
import re
import additional_pfp_tests_remaining_audit as a
p='pfp/tests/test_documented_numbers_are_current.py'
t=ast.parse('\n'.join(a.source(p)))
n=next(n for n in t.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='_SERDE_TYPE' for x in n.targets))
pattern=eval(compile(ast.Expression(n.value),'<read-vetted regex>','eval'),{'re':re})
fixtures={'plain':'#[derive(Serialize)]\npub struct Plain {}','intervening_cfg':'#[derive(Serialize)]\n#[cfg(feature = "enabled")]\npub struct Present {}','comment':'// #[derive(Serialize)] pub struct Imaginary {}','same_name_modules':'mod a { #[derive(Serialize)] pub struct Packet {} }\nmod b { #[derive(Serialize)] pub struct Packet {} }'}
found={k:[name for derives,name in pattern.findall(v) if 'Serialize' in derives or 'Deserialize' in derives] for k,v in fixtures.items()}
assert found=={'plain':['Plain'],'intervening_cfg':[],'comment':['Imaginary'],'same_name_modules':['Packet','Packet']}
assert len(set(found['same_name_modules']))==1
a.write('_probe19.json',{'runtime':sys.version,'source':{'path':p,'sha256':a.row(p)['sha256'],'lines':[46,67]},'fixtures':fixtures,'regex_names':found,'same_name_census_count':1,'limits':['Regex applied only to four inert text examples; no Rust compilation or actual source census.','Shows syntactic query scope and name collapsing, not the actual current documented count.']})
print('serde census misses cfg-interleaved type, counts comment, and collapses module-qualified duplicates')
