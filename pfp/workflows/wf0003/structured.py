"""WF3 keyed slots and native L2 values; raw model answers are never rewritten."""

from copy import deepcopy

from pfp.infrastructure.adapters.pfp_campaign import canonical
from pfp.workflows.wf0002 import workflow as codec
from adversary.infrastructure.providers.anthropic_messages import provider_output_schema


def object_schema(properties):
    return dict(
        type="object", properties=properties, required=list(properties), additionalProperties=False
    )


def answer_schema(spec, required, operations):
    schema = codec.response_schema(spec)
    provided = object_schema(
        dict(
            disposition={"const": "provided"},
            value=dict(type="string", pattern=r"\S", maxLength=160),
            reason={"const": ""},
        )
    )
    missing = object_schema(
        dict(
            disposition={"enum": ["not_applicable", "unresolved"]},
            value={"const": ""},
            reason=dict(type="string", minLength=1, maxLength=160),
        )
    )
    definitions = dict(
        provided=provided, optional={"anyOf": [{"$ref": "#/$defs/provided"}, missing]}
    )
    schema["properties"]["operad_candidates"] = {"const": deepcopy(operations)}
    integers = dict(type="array", items=dict(type="integer"))
    bindings = dict(
        concrete_spans=object_schema(dict(source={"const": "input.values"}, literal=integers)),
        parameter_bindings=object_schema(
            dict(values=integers, arithmetic={"const": "integer_exact"})
        ),
        instantiated_arguments=object_schema(
            dict(operad_id=dict(type="string", minLength=1), arguments=integers)
        ),
        preservation_obligations=object_schema(
            dict(
                all_operands_once={"const": True},
                signed_integers={"const": True},
                rounding={"const": "forbidden"},
            )
        ),
    )
    if spec["checker"] == "integer_sum_v1":
        values = deepcopy(spec["input"]["values"])
        eligible = [
            op["id"]
            for op in operations
            if op["arity"] == 1
            and op["source_colours"] == ["IntegerList"]
            and op["target_colour"] == "Integer"
        ]
        if not eligible:
            raise ValueError("WF3_MINED_INTEGER_LIST_OPERATION_REQUIRED")
        facts = dict(
            concrete_spans=dict(source="input.values", literal=values),
            parameter_bindings=dict(values=values, arithmetic="integer_exact"),
            instantiated_arguments=dict(operad_id=eligible[0], arguments=values),
            preservation_obligations=dict(
                all_operands_once=True, signed_integers=True, rounding="forbidden"
            ),
        )
        for name, value in facts.items():
            definitions[name] = {"const": dict(disposition="provided", value=value, reason="")}
    properties = {}
    for row in codec.catalogue()["slots"]:
        name = row["id"]
        target = (
            name
            if name in bindings and spec["checker"] == "integer_sum_v1"
            else ("provided" if name in required else "optional")
        )
        properties[name] = {"$ref": "#/$defs/" + target}
    schema["properties"]["slot_report"] = object_schema(properties)
    schema["$defs"] = definitions
    return schema


def wire_schema(schema):
    # The shared OpenRouter codec removes $id. Move definitions to the envelope
    # root so its local references retain their meaning after that transform.
    value = provider_output_schema(schema)
    answer = value["properties"]["answer"]
    value["$defs"] = answer.pop("$defs")
    return value


def codec_check(spec, checked):
    if not checked["schema_valid"]:
        return codec.finalize_check(spec, checked)
    view = deepcopy(checked)
    actual = checked["answer"]
    view["answer"]["slot_report"] = [
        dict(
            slot=name,
            **{
                **row,
                "value": canonical(row["value"]).decode()
                if type(row["value"]) is dict
                else row["value"],
            },
        )
        for name, row in actual["slot_report"].items()
    ]
    result = codec.finalize_check(spec, view)
    # Only host checking uses the adapter view. Keep the exact parsed model map.
    result["answer"] = deepcopy(actual)
    result["codec_view"] = "HOST_PROJECTION_OF_KEYED_SLOTS; raw answer map retained"
    return result
