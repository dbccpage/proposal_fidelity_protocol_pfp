"""Retain every emitted record occurrence with exact response-byte custody."""

import json
from hashlib import sha256

from pfp.domain.pfp_ingress import strict_json
from pfp.infrastructure.adapters.pfp_campaign import canonical


def _record_spans(text):
    """Walk actual JSON syntax; do not find keys by searching inside string values."""
    decoder = json.JSONDecoder()
    spans = {}
    targets = {("answer", "operad_candidates"), ("answer", "ddc_moves")}

    def skip(position):
        while position < len(text) and text[position].isspace():
            position += 1
        return position

    def walk(position, path):
        position = skip(position)
        if text[position] == "{":
            position = skip(position + 1)
            while text[position] != "}":
                key, position = decoder.raw_decode(text, position)
                position = skip(position)
                position = walk(position + 1, (*path, key))
                position = skip(position)
                if text[position] == ",":
                    position = skip(position + 1)
            return position + 1
        if text[position] == "[":
            position = skip(position + 1)
            index = 0
            while text[position] != "]":
                start = position
                position = walk(position, (*path, index))
                if path in targets:
                    spans[(*path, index)] = (
                        len(text[:start].encode("utf-8")),
                        len(text[:position].encode("utf-8")),
                    )
                index += 1
                position = skip(position)
                if text[position] == ",":
                    position = skip(position + 1)
            return position + 1
        return decoder.raw_decode(text, position)[1]

    walk(0, ())
    return spans


def collect_emitted(spec, raw, checked):
    digest = sha256(raw).hexdigest()
    result = dict(
        workflow_id="WF2",
        raw_reply_sha256=digest,
        operads=[],
        ddc_moves=[],
        authority_effect="None",
        status="RAW_ONLY",
        residual_text_ledger=[],
    )
    try:
        text = raw.decode("utf-8")
        payload = strict_json(text)
        if type(payload) is not dict or type(payload.get("answer")) is not dict:
            raise ValueError("NO_STRUCTURED_ANSWER")
        spans = _record_spans(text)
    except (UnicodeError, ValueError, IndexError) as exc:
        result["residual_text_ledger"] = [dict(start_byte=0, end_byte=len(raw), reason=str(exc))]
        return result
    result["status"] = "COLLECTED"
    if not checked["schema_valid"]:
        result["residual_text_ledger"].append(
            dict(
                start_byte=0,
                end_byte=len(raw),
                reason="SCHEMA_INVALID; structured records retained in quarantine.",
            )
        )
    previous = {}
    for key, destination in (("operad_candidates", "operads"), ("ddc_moves", "ddc_moves")):
        values = payload["answer"].get(key)
        if type(values) is not list:
            result["residual_text_ledger"].append(dict(reason="MISSING_RECORD_ARRAY:" + key))
            continue
        for index, value in enumerate(values):
            start, end = spans[("answer", key, index)]
            occurrence = f"{destination}:{index:04d}"
            content_digest = sha256(canonical(value)).hexdigest()
            row = dict(
                occurrence_id=occurrence,
                json_pointer=f"/answer/{key}/{index}",
                start_byte=start,
                end_byte=end,
                record=value,
                raw_record_sha256=sha256(raw[start:end]).hexdigest(),
                duplicate_of=previous.get((destination, content_digest)),
                disposition="UNVERIFIED_CANDIDATE"
                if checked.get("operad_structure_valid")
                else "QUARANTINED",
                authority_effect="None",
            )
            previous.setdefault((destination, content_digest), occurrence)
            result[destination].append(row)
    return result
