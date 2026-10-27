"""Finite management-ladder items and exact answer checks (version 2).

No provider I/O. Ground truth never enters the public prompt packet.
"""
from dataclasses import dataclass
import json

from pfp.domain.pfp_ingress import strict_json
from pfp.domain.pilots.fail_closed_gate import FailClosedRefusalGate

VERSION = 'pfp.management-ladder.v2'
SEED = 12015


@dataclass(frozen=True)
class LadderItem:
    item_id: str
    family: str
    rung: int
    split: str
    prompt: str
    payload: dict
    expected: dict

    @property
    def stratum(self):
        return 'composition' if self.family == 'composition' else 'host_solvable'


def item_bank():
    rows=[]
    for split, offset in [('train',0),('held_out',7)]:
        for rung in (1,2,3):
            n=rung+offset
            x,y=11+n,19+n
            a,b=x+2*y,3*x-y
            rows.append(LadderItem(f'{split}-linalg-{rung}','linear_algebra',rung,split,
                f'Solve x+2y={a}, 3x-y={b}. Return sum x+y plus integer witness x,y.',
                dict(a=a,b=b),dict(answer=x+y,witness=dict(x=x,y=y))))
            code='def run():\n'+''.join('    x = 1\n' for _ in range(n))+ '    try:\n        return risky()\n    except:\n        pass\n'
            rows.append(LadderItem(f'{split}-defect-{rung}','seeded_defect',rung,split,
                'Find the bare except. Return {"rule":"BARE_EXCEPT","line":<1-based line>}. Source:\n'+code,
                dict(source=code),dict(rule='BARE_EXCEPT',line=n+4)))
            text=('careful observation ' * (n+1))+'obviously measured'
            rows.append(LadderItem(f'{split}-claim-{rung}','claim_hygiene',rung,split,
                'Locate forbidden word obviously. Return {"matches":[{"token":"obviously","offset":<0-based character offset>}]} in this text:\n'+text,
                dict(text=text),dict(matches=[dict(token='obviously',offset=text.index('obviously'))])))
            # Distinct labels and order in the held-out set; no gold tree in prompt.
            ports=['Code']+[f'Audit.p{offset+i}' for i in range(rung)]+['Receipt']
            ops=[dict(op_id=f'op{offset+i}',inputs=[ports[i]],output=ports[i+1]) for i in range(len(ports)-1)]
            tree='Code'
            for op in ops:
                tree=dict(op=op['op_id'],args=[tree])
            payload=dict(inputs=['Code'],goal='Receipt',ops=ops)
            prompt='Find a smallest planar operation tree. Return {"tree":{"op":id,"args":[...]},"op_count":integer}. Leaves are input colour strings. Inventory: '+json.dumps(payload,separators=(',',':'))
            rows.append(LadderItem(f'{split}-composition-{rung}','composition',rung,split,prompt,payload,
                dict(tree=tree,op_count=len(ops))))
    return tuple(rows)


def canonical_answer(value):
    return 'ANSWER: '+json.dumps(value,sort_keys=True,separators=(',',':'))


def grade_answer(item, text, *, composition_checker=None):
    """Use only the canonical ANSWER line; no arm/model inputs reach this gate."""
    result=dict(accepted=False,reason='MALFORMED',obligations_total=2,obligations_discharged=0)
    if type(text) is not str:
        return result
    lines=[line for line in text.splitlines() if line.startswith('ANSWER: ')]
    if len(lines)!=1:
        return result
    try:
        value=strict_json(lines[0][8:])
    except (ValueError,TypeError,RecursionError):
        return result
    if not isinstance(value,dict):
        return result
    if value.get('status') == 'REFUSED':
        return {**result,'reason':'REFUSED'}
    if item.family=='linear_algebra':
        observed=FailClosedRefusalGate.evaluate_candidate_payload('PFP-01-EXACT-LINALG',item.expected['answer'],value)
        witness=value.get('witness',{})
        correct=(observed.is_accepted and set(value)=={'answer','witness'}
            and type(witness) is dict and set(witness)=={'x','y'}
            and all(type(witness.get(key)) is int for key in ('x','y'))
            and witness['x']+2*witness['y']==item.payload['a']
            and 3*witness['x']-witness['y']==item.payload['b'])
    elif item.family=='composition':
        if composition_checker is None:
            return {**result,'reason':'CHECKER_UNAVAILABLE'}
        correct=composition_checker(item,value)
    else:
        # Strict canonical comparison rejects booleans in integer positions.
        correct=json.dumps(value,sort_keys=True,separators=(',',':')) == json.dumps(item.expected,sort_keys=True,separators=(',',':'))
    return {**result,'accepted':bool(correct),'reason':'ACCEPTED' if correct else 'WRONG_ANSWER',
        'obligations_discharged':2 if correct else 0}


def control_answers(item):
    return (('',False),('noise',False),('ANSWER: {}',False),
        (canonical_answer(item.expected),True),
        (canonical_answer(item.expected)+'\n'+canonical_answer(item.expected),False),
        ('ANSWER: {"answer":1,"answer":1}',False),
        (canonical_answer({**item.expected,'status':'REFUSED'}),False))


def select_calibration_items(rows, bank, count=2):
    failures={row['item_id'] for row in rows if not row['accepted']}
    eligible=[item for item in bank if item.split=='train']
    # Deterministic signal selection; no failure is manufactured if A0 is perfect.
    return tuple(sorted(eligible,key=lambda item:(item.item_id not in failures,-item.rung,item.item_id))[:count])
