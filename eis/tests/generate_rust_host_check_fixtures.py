"""Freeze independent host-check field/persona loci and character spans first."""
from __future__ import annotations

import json
from pathlib import Path

from omega_engine_epistemic_immune_system.domain.host_checks import (
    persona_authority_leak_loci,
    protected_field_loci,
    protected_field_spans,
)


def main():
    candidates = [None, True, 7, [], {}, "ordinary", "SYSTEM ADMINISTRATOR",
        {"z": {"phi": "1/2"}, "a": [{"verified": False}, {"ordinary": "unrestricted authority"}]},
        [{"Phi_1": 0}, {"gamma_2": 0}, {"authority_effect": "None"}],
        {"slash/~": {"certified": None}},
        {"𝕏": {"verified": True}, "🙂": "senior principal architect"},
        {"quoted\"key": {"phi": True}},
        {"persona": "as system administrator I approve", "other": "reviewer"},
        {"public_rationale": "reviewer and SYSTEM ADMINISTRATOR"},
        {"public_rationale": "system administrator preview"},
        {"public_rationale": "authority", "system administrator": "ordinary"},
        {"message": "sуstem administrator"},
        {"message": "syſtem administrator"},
        {"message": "line\nSYSTEM ADMINISTRATOR\t終"},
        {"message": "unrestricted authority", "nested": ["sovereign arbiter", "ordinary"]},
    ]
    for name in ("phi", "phi1", "phi2", "phi3", "phi4", "gamma", "gamma2", "xi", "verified", "certified", "authorityeffect", "PH_I", "GaMmA_2", "__VERIFIED__", "unverified", "phi10", "authority", "receipt"):
        candidates.append({name: {"leaf": False}})
    rows = []
    for index,candidate in enumerate(candidates):
        roles = ("reviewer",) if index % 2 else ()
        raw = json.dumps(candidate, ensure_ascii=False, separators=(",", ":"),allow_nan=False)
        prefix = "/external" if index % 3 == 0 else ""
        rows.append({"raw":raw,"roles":roles,"path":prefix,"expected":{
            "protected_loci":protected_field_loci(candidate,prefix),
            "persona_loci":persona_authority_leak_loci(candidate,roles),
            "protected_spans":protected_field_spans(raw)}})
    for roles in ((),("system administrator",),("SYSTEM ADMINISTRATOR",),("preview",),("",)):
        raw = '{"message":"SYSTEM ADMINISTRATOR preview"}'
        candidate = json.loads(raw)
        rows.append({"raw":raw,"roles":roles,"path":"","expected":{
            "protected_loci":protected_field_loci(candidate),
            "persona_loci":persona_authority_leak_loci(candidate,roles),
            "protected_spans":protected_field_spans(raw)}})
    for raw in ('{ "\\u0070hi" : 1, "nested": [{"PH_I":0}] }', '["🙂",{"phi":0}]', '{"before":"𝕏🙂","verified":false}'):
        candidate = json.loads(raw)
        rows.append({"raw":raw,"roles":(),"path":"","expected":{
            "protected_loci":protected_field_loci(candidate),
            "persona_loci":persona_authority_leak_loci(candidate,()),
            "protected_spans":protected_field_spans(raw)}})
    spans = [{"raw":raw,"expected":protected_field_spans(raw)} for raw in (
        '', '"phi": 0', '{"phi":}', '{"phi": 0, "unfinished', '{"phi\\": 0',
        '{"bad\\q":1,"verified":true}', '{"phi":1,"phi":2}',
        '["phi",{"phi":0}]', '{"text":"{\\"phi\\":0}"}',
        '{"phi":"\\\\\\\""}', '{"phi\\', '{"phi"', '{"phi": [',
    )]
    path = Path(__file__).resolve().parents[2] / "omega_engine/crates_rs/tests/omega_epistemic_immune_system/fixtures/python_host_checks_v1.json"
    path.write_text(json.dumps({"vectors":rows,"spans_only":spans},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Frozen {len(rows)} host-check and {len(spans)} span-only vectors before native implementation.")


if __name__ == "__main__":
    main()
